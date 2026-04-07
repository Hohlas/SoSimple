# Triple Barrier Classification — Implementation Plan

> **Status note (2026-04-07):** This is the original implementation plan for bringing `triple_barrier` online. Core implementation from this document already exists in the codebase. For current continuation, calibration, first-touch relabeling, and final verdict, use [docs/superpowers/plans/2026-04-07-triple-barrier-hardening.md](2026-04-07-triple-barrier-hardening.md).

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add parallel ML task `triple_barrier` — 12 binary classification targets predicting P(TP hit before SL) for 6 SL/TP combos × 2 directions.

**Architecture:** New task alongside existing `regression_updn`. Shared Transformer encoder, BCEWithLogitsLoss, labels computed from raw MFE before normalization. Separate checkpoint, signals CSV, and MT4 function.

**Tech Stack:** Python 3.11, PyTorch, NumPy, Pandas, scikit-learn (AUC), MQL4

**Spec:** [docs/superpowers/specs/2026-03-22-triple-barrier-design.md](../specs/2026-03-22-triple-barrier-design.md)

---

## File Structure

### Modified files
| File | Responsibility |
|------|---------------|
| `processing/label_signals.py` | Add `label_triple_barrier()` — compute 12 binary labels |
| `processing/label_main.py` | Call `label_triple_barrier()` in pipeline |
| `ML/data_loader.py` | Add `triple_barrier` target loading (12 columns) |
| `ML/utils.py` | Add `compute_binary_classification_metrics()` |
| `ML/train.py` | Add `--task triple_barrier` branch (BCEWithLogitsLoss, AUC) |
| `ML/evaluate_test.py` | Add TB evaluation on test set |
| `ML/threshold_analysis.py` | Add `analyze_thresholds_tb()` — realistic PF |
| `API/generate_signals.py` | Add `--task triple_barrier` → `ml_signals_tb.csv` |
| `ML/compare_architectures.py` | Support `--task triple_barrier` |
| `ML/optimize.py` | Support `--task triple_barrier` |

### New files
| File | Responsibility |
|------|---------------|
| `MT/MQL4/Include/lib_ML_Signal_TB.mqh` | MT4 integration for TB signals |

---

## Task 1: Labeling — `label_triple_barrier()`

**Files:**
- Modify: `processing/label_signals.py` (add function at end, before `if __name__`)
- Modify: `processing/label_main.py:328-329` (add call after `label_updn`)

### Step 1.1: Verify raw Up/Dn units

Before writing labels, confirm what units `up_24`/`dn_24` use after `label_updn()`.

- [ ] **Run quick diagnostic:**

```bash
cd ~/git/SoSimple
source .venv/bin/activate
python -c "
import pandas as pd
df = pd.read_csv('DATA/Nero_train_labeled.csv', sep=';', nrows=5)
print('Columns:', [c for c in df.columns if 'up_' in c or 'dn_' in c or c == 'ATR'])
print(df[['ATR', 'up_12', 'dn_12', 'up_24', 'dn_24']].head())
"
```

**Note:** These values are NORMALIZED (post-pipeline). To see raw values, run `label_main.py --no-normalize` or inspect mid-pipeline. The key question: are raw `up_24` values comparable to `ATR`? If `up_24 ≈ 0.1-0.5` and `ATR ≈ 20-50`, they're in different units → divide. If `up_24 ≈ 10-100` and `ATR ≈ 20-50`, they're raw price → divide.

### Step 1.2: Add `label_triple_barrier()` to `label_signals.py`

- [ ] **Add function at end of `processing/label_signals.py` (before `if __name__`):**

```python
# ─── Triple Barrier Labels ────────────────────────────────────────────────

# SL/TP grid (in ATR units)
TB_SL_LEVELS = [2, 3]
TB_TP_LEVELS = [3, 6, 9]

# Column names for 12 binary targets
TB_TARGET_NAMES = []
for sl in TB_SL_LEVELS:
    for tp in TB_TP_LEVELS:
        TB_TARGET_NAMES.append(f'buy_sl{sl}_tp{tp}')
for sl in TB_SL_LEVELS:
    for tp in TB_TP_LEVELS:
        TB_TARGET_NAMES.append(f'sell_sl{sl}_tp{tp}')


def label_triple_barrier(df, debug=False):
    """
    Compute 12 binary Triple Barrier labels from raw MFE values.

    Must be called AFTER label_updn() and BEFORE normalize_rowwise().
    Uses raw up_24/dn_24 (price units) and ATR to determine if
    TP barrier was hit before SL barrier within 24 bars.

    Ambiguous cases (both barriers reached) → label = 0 (conservative).

    Args:
        df: DataFrame with raw up_24, dn_24, ATR columns.
        debug: Print statistics.

    Returns:
        DataFrame with 12 added binary columns.
    """
    up_raw = pd.to_numeric(df['up_24'], errors='coerce').fillna(0.0)
    dn_raw = pd.to_numeric(df['dn_24'], errors='coerce').fillna(0.0)
    atr = pd.to_numeric(df['ATR'], errors='coerce').fillna(1.0)

    # Convert to ATR units
    up_atr = up_raw / atr.replace(0, 1.0)
    dn_atr = dn_raw / atr.replace(0, 1.0)

    for sl in TB_SL_LEVELS:
        for tp in TB_TP_LEVELS:
            # BUY: price up >= TP*ATR AND price down < SL*ATR
            df[f'buy_sl{sl}_tp{tp}'] = ((up_atr >= tp) & (dn_atr < sl)).astype(int)
            # SELL: mirror
            df[f'sell_sl{sl}_tp{tp}'] = ((dn_atr >= tp) & (up_atr < sl)).astype(int)

    if debug:
        total = len(df)
        print(f"\n[TRIPLE BARRIER] Labels computed for {total} rows:")
        for name in TB_TARGET_NAMES:
            ones = df[name].sum()
            print(f"  {name}: {ones} ({ones/total*100:.1f}%)")

    return df
```

### Step 1.3: Wire into `label_main.py`

- [ ] **Modify `processing/label_main.py` — add import and call:**

After line 54 (`from label_signals import label_all, label_updn`), add:
```python
from label_signals import label_all, label_updn, label_triple_barrier
```

After line 328 (`labeled_df = label_updn(labeled_df, debug=args.debug)`), add:
```python
    # 3c. Triple Barrier labels (binary, before normalization)
    print(f"\nРазметка Triple Barrier таргетов...")
    labeled_df = label_triple_barrier(labeled_df, debug=args.debug)
```

Update the final print (line 352) to include TB targets:
```python
    print(f"Метки: signal, predict, up_12..dn_48, buy_sl*_tp*, sell_sl*_tp*")
```

### Step 1.4: Regenerate dataset

- [ ] **Run pipeline to regenerate labeled CSVs:**

```bash
cd ~/git/SoSimple
python processing/label_main.py --input MT/MQL4/Files/Nero.csv --debug
```

Expected output: TB label statistics printed, 12 new columns in output CSVs.

- [ ] **Verify new columns exist and have reasonable distributions:**

```bash
python -c "
import pandas as pd
df = pd.read_csv('DATA/Nero_train_labeled.csv', sep=';', nrows=5)
tb_cols = [c for c in df.columns if c.startswith('buy_sl') or c.startswith('sell_sl')]
print('TB columns:', tb_cols)
print(f'Count: {len(tb_cols)}')
print(df[tb_cols].describe())
"
```

Expected: 12 TB columns, all values 0 or 1, reasonable percentage of 1s (expect 5-30% for buy_sl2_tp3, <5% for buy_sl2_tp9).

- [ ] **Commit:**

```bash
git add processing/label_signals.py processing/label_main.py
git commit -m "feat: add label_triple_barrier() — 12 binary TB targets from MFE"
```

---

## Task 2: Data Loader — `triple_barrier` target

**Files:**
- Modify: `ML/data_loader.py`

### Step 2.1: Add TB constants and target loading

- [ ] **Add constants after line 80 (`UPDN_TARGETS = [...]`):**

```python
# Triple Barrier targets (12 binary: 6 BUY + 6 SELL)
TB_TARGET = 'triple_barrier'
TB_SL_LEVELS = [2, 3]
TB_TP_LEVELS = [3, 6, 9]
TB_TARGET_NAMES = []
for _sl in TB_SL_LEVELS:
    for _tp in TB_TP_LEVELS:
        TB_TARGET_NAMES.append(f'buy_sl{_sl}_tp{_tp}')
for _sl in TB_SL_LEVELS:
    for _tp in TB_TP_LEVELS:
        TB_TARGET_NAMES.append(f'sell_sl{_sl}_tp{_tp}')
```

### Step 2.2: Modify `create_data_loaders()` to handle TB target

- [ ] **In `create_data_loaders()`, update the `regression` flag logic (around line 303):**

```python
    regression = (target == REGRESSION_TARGET) or (target == UPDN_REGRESSION_TARGET)
    multi_target = (target == UPDN_REGRESSION_TARGET)
    triple_barrier = (target == TB_TARGET)
```

- [ ] **In `load_or_parse_data()`, add TB branch for target extraction (around line 347):**

After the `if multi_target:` block, add:
```python
        elif triple_barrier:
            y = df[TB_TARGET_NAMES].values.astype(np.float32)  # shape (n, 12)
```

- [ ] **In the dataset creation section (around line 411), handle TB:**

```python
    train_dataset = FractalSequenceDataset(
        X_train_norm, y_train, mask_train,
        regression=(regression or triple_barrier),
    )
    val_dataset = FractalSequenceDataset(
        X_val_norm, y_val, mask_val,
        regression=(regression or triple_barrier),
    )
```

The `regression=True` flag ensures y is treated as float (no LABEL_MAP mapping), which is correct for binary labels stored as float32.

- [ ] **Add TB statistics printing (after line 384):**

```python
    elif triple_barrier:
        for name, y in [('Train', y_train), ('Val', y_val)]:
            print(f"  {name} TB targets: shape={y.shape}")
            for i, col in enumerate(TB_TARGET_NAMES):
                ones = y[:, i].sum()
                total = len(y)
                print(f"    {col}: {int(ones)}/{total} ({ones/total*100:.1f}%)")
```

### Step 2.3: Modify `create_test_loader()` similarly

- [ ] **Add TB handling in `create_test_loader()` (around line 472):**

```python
    triple_barrier = (target == TB_TARGET)
```

And in the target extraction:
```python
        elif triple_barrier:
            y = df[TB_TARGET_NAMES].values.astype(np.float32)
```

And fix dataset creation `regression` flag:
```python
    dataset = FractalSequenceDataset(X, y, mask, regression=(regression or triple_barrier))
```

### Step 2.4: Verify data loading

- [ ] **Test that TB data loads correctly:**

```bash
python -c "
from ML.data_loader import create_data_loaders, TB_TARGET
train_loader, val_loader, _ = create_data_loaders(
    batch_size=32, target=TB_TARGET, clear_cache=True
)
X, y, mask = next(iter(train_loader))
print(f'X: {X.shape}, y: {y.shape}, mask: {mask.shape}')
print(f'y sample: {y[0]}')
print(f'y dtype: {y.dtype}')
assert y.shape[1] == 12, f'Expected 12 targets, got {y.shape[1]}'
print('OK')
"
```

Expected: `X: (32, 100, 20), y: (32, 12), mask: (32, 100)`

- [ ] **Commit:**

```bash
git add ML/data_loader.py
git commit -m "feat: data_loader support for triple_barrier target (12 binary)"
```

---

## Task 3: Metrics — binary classification utilities

**Files:**
- Modify: `ML/utils.py`

### Step 3.1: Add binary classification metrics

- [ ] **Add imports at the top of `ML/utils.py`:**

```python
from sklearn.metrics import roc_auc_score
```

- [ ] **Add function after `compute_multitarget_regression_metrics()`:**

```python
def compute_binary_classification_metrics(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    target_names: list[str] | None = None,
    threshold: float = 0.5,
) -> dict:
    """
    Metrics for multi-target binary classification (Triple Barrier).

    Args:
        y_true: shape (n_samples, n_targets), binary {0, 1}
        y_pred_proba: shape (n_samples, n_targets), probabilities [0, 1]
        target_names: list of target names for per-target reporting
        threshold: classification threshold for precision/recall

    Returns:
        Dict with per-target AUC, precision, recall, and mean AUC.
    """
    n_targets = y_true.shape[1]
    if target_names is None:
        target_names = [f'target_{i}' for i in range(n_targets)]

    per_target = {}
    aucs = []

    for i in range(n_targets):
        name = target_names[i]
        yt = y_true[:, i]
        yp = y_pred_proba[:, i]

        # AUC (handle edge case: only one class present)
        n_pos = yt.sum()
        n_neg = len(yt) - n_pos
        if n_pos == 0 or n_neg == 0:
            auc = 0.5  # uninformative
        else:
            auc = float(roc_auc_score(yt, yp))

        # Precision / Recall at threshold
        yp_bin = (yp >= threshold).astype(int)
        tp = ((yp_bin == 1) & (yt == 1)).sum()
        fp = ((yp_bin == 1) & (yt == 0)).sum()
        fn = ((yp_bin == 0) & (yt == 1)).sum()

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        pos_rate = float(n_pos / len(yt))

        per_target[name] = {
            'auc': auc,
            'precision': precision,
            'recall': recall,
            'pos_rate': pos_rate,
            'n_pos': int(n_pos),
        }
        aucs.append(auc)

    mean_auc = float(np.mean(aucs))

    return {
        'mean_auc': mean_auc,
        'per_target': per_target,
    }
```

- [ ] **Verify:**

```bash
python -c "
import numpy as np
from ML.utils import compute_binary_classification_metrics
y_true = np.array([[1,0],[0,1],[1,1],[0,0]])
y_pred = np.array([[0.8,0.2],[0.3,0.9],[0.7,0.6],[0.1,0.1]])
m = compute_binary_classification_metrics(y_true, y_pred, ['a','b'])
print(f'mean_auc: {m[\"mean_auc\"]:.3f}')
print(m['per_target'])
"
```

- [ ] **Commit:**

```bash
git add ML/utils.py
git commit -m "feat: add compute_binary_classification_metrics for TB"
```

---

## Task 4: Training — `triple_barrier` task in `train.py`

**Files:**
- Modify: `ML/train.py`

### Step 4.1: Add TB imports and constants

- [ ] **Add imports (after existing data_loader imports, line 70):**

```python
from ML.data_loader import create_data_loaders, INV_LABEL_MAP, N_FRACTAL_FEATURES, UPDN_TARGETS, UPDN_REGRESSION_TARGET, TB_TARGET, TB_TARGET_NAMES
from ML.utils import (
    set_seed, compute_metrics, compute_regression_metrics,
    compute_multitarget_regression_metrics,
    compute_binary_classification_metrics,
    count_parameters, get_device,
)
```

### Step 4.2: Add TB branch in `train_model()`

- [ ] **Update task detection (around line 343):**

```python
    multi_target = (task == 'regression_updn')
    triple_barrier = (task == 'triple_barrier')
    regression = (task == 'regression') or multi_target
```

**Important:** `regression` stays False for TB. But `train_one_epoch()` must be called with `regression=True` for TB so it doesn't squeeze the output. We handle this below.

- [ ] **Update target_col selection (around line 354-359):**

```python
    if triple_barrier:
        target_col = TB_TARGET
    elif multi_target:
        target_col = UPDN_REGRESSION_TARGET
    elif regression:
        target_col = 'predict'
    else:
        target_col = 'signal'
```

- [ ] **Update num_classes (around line 371):**

```python
    if triple_barrier:
        num_classes = len(TB_TARGET_NAMES)  # 12
    elif multi_target:
        num_classes = len(UPDN_TARGETS)     # 6
    elif regression:
        num_classes = 1
    else:
        num_classes = 3
```

- [ ] **Update loss function (around line 386):**

```python
    if triple_barrier:
        # Compute pos_weight from training data for class imbalance
        y_train_all = []
        for _, y_batch, _ in train_loader:
            y_train_all.append(y_batch.numpy())
        y_train_np = np.concatenate(y_train_all)
        n_pos = y_train_np.sum(axis=0)
        n_neg = len(y_train_np) - n_pos
        pos_weight = torch.tensor(n_neg / (n_pos + 1e-6), dtype=torch.float32).to(device)
        loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight).to(device)
    elif regression:
        ...  # existing code
```

### Step 4.3: Add TB validation function

- [ ] **Add after `validate_regression()` function:**

```python
@torch.no_grad()
def validate_triple_barrier(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> tuple[float, dict]:
    """Validation for triple_barrier task."""
    model.eval()
    total_loss = 0.0
    n_batches = 0
    all_preds = []
    all_targets = []

    for X_batch, y_batch, mask_batch in val_loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        mask_batch = mask_batch.to(device)

        logits = model(X_batch, mask=mask_batch)
        loss = loss_fn(logits, y_batch)

        total_loss += loss.item()
        n_batches += 1

        proba = torch.sigmoid(logits).cpu().numpy()
        all_preds.append(proba)
        all_targets.append(y_batch.cpu().numpy())

    all_preds = np.concatenate(all_preds)
    all_targets = np.concatenate(all_targets)

    metrics = compute_binary_classification_metrics(
        all_targets, all_preds, TB_TARGET_NAMES
    )

    return total_loss / n_batches, metrics
```

### Step 4.4: Wire TB into training loop

- [ ] **In the training loop (around line 416), add TB history branch:**

```python
    if triple_barrier:
        history = {
            'train_loss': [], 'val_loss': [],
            'val_mean_auc': [], 'lr': [],
        }
        metric_name = 'mean_auc'
        if not silent:
            print(f"\n{'Epoch':>5} | {'Train Loss':>10} | {'Val Loss':>10} | "
                  f"{'Mean AUC':>10} | {'LR':>10}")
    elif regression:
        ...  # existing
```

- [ ] **In the `train_one_epoch` call (around line 451), pass `regression=True` for TB:**

The model outputs `(batch, 12)` and y is `(batch, 12)`. With `regression=True`, `train_one_epoch` uses the multi-target path: `loss = loss_fn(logits, y_batch)` which works for BCEWithLogitsLoss.

```python
        train_loss = train_one_epoch(
            model, train_loader, loss_fn, optimizer, device,
            regression=(regression or triple_barrier),
        )
```

- [ ] **In the epoch validation (around line 455), add TB branch:**

```python
        if triple_barrier:
            val_loss, metrics = validate_triple_barrier(model, val_loader, loss_fn, device)
            val_metric = metrics['mean_auc']

            history['train_loss'].append(train_loss)
            history['val_loss'].append(val_loss)
            history['val_mean_auc'].append(metrics['mean_auc'])
            history['lr'].append(optimizer.param_groups[0]['lr'])

            if not silent:
                print(f"{epoch:>5} | {train_loss:>10.4f} | {val_loss:>10.4f} | "
                      f"{metrics['mean_auc']:>10.4f} | "
                      f"{optimizer.param_groups[0]['lr']:>10.6f}")
        elif regression:
            ...  # existing
```

- [ ] **Update checkpoint suffix (around line 524):**

```python
            if triple_barrier:
                suffix = '_tb'
            elif multi_target:
                suffix = '_updn'
            elif regression:
                suffix = '_regression'
            else:
                suffix = ''
```

- [ ] **Update results printing for TB (around line 559):**

```python
            if triple_barrier:
                print(f"  Mean AUC: {best_metrics.get('mean_auc', 0):.4f}")
                if 'per_target' in best_metrics:
                    for name, tm in best_metrics['per_target'].items():
                        print(f"    {name}: AUC={tm['auc']:.4f}, pos_rate={tm['pos_rate']:.1%}")
```

### Step 4.5: Fix post-training plots and logging (Critical — prevents runtime crash)

These sections assume classification or regression metrics. TB has neither `confusion_matrix` nor `val_f1_macro` in history.

- [ ] **In `_plot_training_curves()` (around line 729), add TB guard:**

Add at the top of the function:
```python
    # TB has different history keys — skip classification/regression curves
    if 'val_mean_auc' in history:
        # Simple 2-panel plot: loss + AUC
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].plot(history['train_loss'], label='Train')
        axes[0].plot(history['val_loss'], label='Val')
        axes[0].set_title('Loss'); axes[0].legend()
        axes[1].plot(history['val_mean_auc'], label='Mean AUC')
        axes[1].set_title('Validation Mean AUC'); axes[1].legend()
        suffix = '_tb'
        fig.savefig(PLOTS_DIR / f'training_curves_{model_name}{suffix}.png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        return
```

- [ ] **In post-training plot section (around line 574), add TB guard:**

Before the `if not regression:` block that calls `_plot_confusion_matrix()`:
```python
    if triple_barrier:
        pass  # No confusion matrix for TB — just training curves
    elif not regression:
        ...  # existing confusion matrix plot
```

- [ ] **In `_log_experiment()` (around line 686), add TB branch:**

```python
    if triple_barrier:
        log_suffix = '_tb'
        row['val_mean_auc'] = best_metrics.get('mean_auc', 0)
    elif regression:
        ...  # existing
```

### Step 4.6: Update CLI args

- [ ] **Update argparse choices (at the bottom of `train.py`):**

Find the `--task` argument and add `triple_barrier`:
```python
    parser.add_argument('--task', choices=['classification', 'regression', 'regression_updn', 'triple_barrier'], default='classification')
```

### Step 4.7: Update `ML/experiment_logger.py`

- [ ] **Add `val_mean_auc` column to `CSV_COLUMNS`** so TB experiments are properly logged.
- [ ] **In the logging function, add TB branch** that logs `mean_auc` and `_tb` suffix.

### Step 4.8: Verify training runs

- [ ] **Run quick training (2 epochs) to verify everything works:**

```bash
python -m ML.train --model transformer --task triple_barrier --epochs 2 --batch_size 256 --seed 42
```

Expected: Training starts, mean AUC printed per epoch, checkpoint saved as `transformer_tb_best.pt`.

- [ ] **Commit:**

```bash
git add ML/train.py ML/experiment_logger.py
git commit -m "feat: train.py support for --task triple_barrier (BCEWithLogitsLoss, AUC)"
```

---

## Task 5: `compare_architectures.py` and `optimize.py`

**Files:**
- Modify: `ML/compare_architectures.py`
- Modify: `ML/optimize.py`

### Step 5.1: Update compare_architectures.py

- [ ] **Add `triple_barrier` to `--task` choices** (find argparse section):

```python
parser.add_argument('--task', choices=['classification', 'regression', 'regression_updn', 'triple_barrier'], ...)
```

No other changes needed — `train_model()` handles the rest.

### Step 5.2: Update optimize.py

- [ ] **Add `triple_barrier` to `--task` choices.**

- [ ] **Update the objective function** to use `mean_auc` when task is `triple_barrier`:

Find where it reads `best_metric` from the training result and ensure it handles `mean_auc`.

- [ ] **Commit:**

```bash
git add ML/compare_architectures.py ML/optimize.py
git commit -m "feat: compare_architectures and optimize support triple_barrier"
```

---

## Task 6: Full Training Run

- [ ] **Run full training with Transformer:**

```bash
python -m ML.train --model transformer --task triple_barrier --epochs 50 --seed 42
```

- [ ] **Record results:** Note the best mean AUC and per-target AUC values. Check for degenerate targets (AUC ≈ 0.50 means model can't predict that target — likely too few positive samples).

---

## Task 7: OOS Evaluation — `evaluate_test.py`

**Files:**
- Modify: `ML/evaluate_test.py`

### Step 7.1: Add TB evaluation

- [ ] **Add TB imports:**

```python
from ML.data_loader import ..., TB_TARGET, TB_TARGET_NAMES
from ML.utils import ..., compute_binary_classification_metrics
```

- [ ] **Add TB branch in `run_evaluation()`:**

Handle loading TB checkpoint (`_tb` suffix), running inference with sigmoid, computing binary metrics, and writing TB-specific report.

- [ ] **Add TB report generation** that includes per-target AUC, precision, recall.

- [ ] **Run:**

```bash
python -m ML.evaluate_test --task triple_barrier --model transformer
```

- [ ] **Commit:**

```bash
git add ML/evaluate_test.py
git commit -m "feat: evaluate_test supports triple_barrier OOS evaluation"
```

---

## Task 8: Threshold Analysis — realistic PF

**Files:**
- Modify: `ML/threshold_analysis.py`

### Step 8.1: Add `analyze_thresholds_tb()`

This is the key deliverable — PF that directly corresponds to MT4 trading with fixed SL/TP.

- [ ] **Add function:**

```python
def analyze_thresholds_tb(y_pred_proba, y_true, target_names, n_thresholds=50):
    """
    Threshold analysis for Triple Barrier.

    For each SL/TP combo and threshold theta:
    - Count trades where P(TP hit) > theta
    - PF = (wins * TP) / (losses * SL)
    - Losses include timeouts (conservative — counted as full SL)
    """
    results = []

    for i, name in enumerate(target_names):
        # Parse SL/TP from name: "buy_sl2_tp6" → sl=2, tp=6
        parts = name.split('_')
        direction = parts[0]  # 'buy' or 'sell'
        sl = int(parts[1][2:])  # 'sl2' → 2
        tp = int(parts[2][2:])  # 'tp6' → 6

        proba = y_pred_proba[:, i]
        true = y_true[:, i]

        thresholds = np.linspace(0.3, 0.95, n_thresholds)

        for theta in thresholds:
            mask = proba > theta
            n_trades = mask.sum()
            if n_trades < 10:
                continue

            wins = true[mask].sum()
            losses = n_trades - wins

            profit = wins * tp
            loss_val = losses * sl
            pf = profit / loss_val if loss_val > 0 else float('inf')
            win_rate = wins / n_trades

            results.append({
                'target': name,
                'direction': direction,
                'sl': sl,
                'tp': tp,
                'theta': round(float(theta), 4),
                'trades': int(n_trades),
                'wins': int(wins),
                'win_rate': round(float(win_rate), 4),
                'pf': round(float(pf), 4),
                'profit': round(float(profit), 2),
                'loss': round(float(loss_val), 2),
            })

    return pd.DataFrame(results)
```

### Step 8.2: Add CLI support and report generation

- [ ] **Add `--task triple_barrier` to argparse.**

- [ ] **Generate markdown report** with best theta per SL/TP combo, sorted by PF.

- [ ] **Run:**

```bash
python -m ML.threshold_analysis --task triple_barrier --model transformer
```

- [ ] **Commit:**

```bash
git add ML/threshold_analysis.py
git commit -m "feat: threshold_analysis with realistic PF for triple_barrier"
```

---

## Task 9: Signal Generation — `ml_signals_tb.csv`

**Files:**
- Modify: `API/generate_signals.py`

### Step 9.1: Add TB signal generation

- [ ] **Add function `generate_tb_signals()`:**

For each row:
1. Run model → 12 probabilities (after sigmoid)
2. Filter: P > theta
3. Compute EV = P × TP - (1-P) × SL for each passing target
4. Pick best EV → determine signal, sl_atr, tp_atr

- [ ] **Output format:**

```
time;signal;sl_atr;tp_atr;prob;ev
```

- [ ] **Add `--task triple_barrier` to CLI:**

```bash
python -m API.generate_signals --task triple_barrier --theta 0.6
```

- [ ] **Verify output:**

```bash
head -5 MT/MQL4/Files/ml_signals_tb.csv
wc -l MT/MQL4/Files/ml_signals_tb.csv
```

- [ ] **Commit:**

```bash
git add API/generate_signals.py
git commit -m "feat: generate_signals supports triple_barrier → ml_signals_tb.csv"
```

---

## Task 10: MT4 Integration — `lib_ML_Signal_TB.mqh`

**Files:**
- Create: `MT/MQL4/Include/lib_ML_Signal_TB.mqh` (UTF-16LE encoding!)

### Step 10.1: Write MT4 library

- [ ] **Create `lib_ML_Signal_TB.mqh`** with:
  - `TB_INIT()` — load ml_signals_tb.csv (same pattern as ML_INIT in lib_ML_Signal.mqh)
  - `TB_FindSignal()` — binary search by time (same pattern)
  - `ML_TRADE_TB()` — open orders using SL/TP from CSV columns
  - Diagnostic counters for reporting

### Step 10.2: Integrate into INPUT.mqh

- [ ] **Add `case 5: ML_TRADE_TB();`** in the iSignal switch inside INPUT.mqh

### Step 10.3: Test in MT4

- [ ] **Update VERSION in `$o$imple.mq4`**
- [ ] **Copy `ml_signals_tb.csv` to tester/files/**
- [ ] **Run Strategy Tester with iSignal=5, Tper=24**
- [ ] **Compare MT4 PF with Python PF** — the gap should be < 20%

- [ ] **Commit:**

```bash
git add MT/MQL4/Include/lib_ML_Signal_TB.mqh MT/MQL4/Include/INPUT.mqh
git commit -m "feat: MT4 integration for Triple Barrier signals (iSignal=5)"
```

---

## Task 11: Update Documentation

- [ ] **Update CHANGELOG.md** with results
- [ ] **Update AGENTS.md** status table (add Triple Barrier row)
- [ ] **Update docs/DATA_FLOW.md** with TB labeling step

- [ ] **Commit:**

```bash
git add CHANGELOG.md AGENTS.md docs/DATA_FLOW.md
git commit -m "docs: add Triple Barrier to changelog and project docs"
```

---

## Execution Order Summary

| Task | Description | Depends on | ~Time |
|------|-------------|------------|-------|
| 1 | Labeling | — | 15 min |
| 2 | Data Loader | Task 1 | 10 min |
| 3 | Metrics | — | 5 min |
| 4 | Training | Tasks 2, 3 | 15 min |
| 5 | Compare/Optimize | Task 4 | 5 min |
| 6 | Full Training | Task 4 | 5 min (launch) |
| 7 | OOS Evaluation | Task 6 | 10 min |
| 8 | Threshold Analysis | Task 7 | 10 min |
| 9 | Signal Generation | Task 8 | 10 min |
| 10 | MT4 Integration | Task 9 | 20 min |
| 11 | Documentation | Task 10 | 5 min |

**Parallelizable:** Tasks 1+3 can run in parallel. Tasks 5+7+8 share code but are sequential.
