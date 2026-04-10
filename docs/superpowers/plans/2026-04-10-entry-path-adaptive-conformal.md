# Entry Path Adaptive Conformal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить более сильный adaptive conformal-слой поверх уже замороженного `A @ 7.5%`, где ширина интервала зависит от сделки, а не остаётся общей для всего набора.

**Architecture:** План не трогает замороженный checkpoint `entry_path_v1` и не переучивает основную модель. Сначала добавляется отдельный export-путь для `train/validation/test` предсказаний `entry_path_v1`, затем поверх этих артефактов обучается маленький `LightGBMRegressor`, который предсказывает `log(1 + |true_ret_24 - pred_ret_24|)` на всех активных строках train. После этого на `validation` считается adaptive conformal через нормированные остатки, выбирается победитель среди правил по нижней границе и ширине, а на `test` применяется уже замороженное правило.

**Tech Stack:** Python 3.11+, pandas, numpy, torch, lightgbm, pytest

---

## File Map

- `ML/data_loader.py`
  Назначение: дать упорядоченный loader для `train`, `validation`, `test`, чтобы можно было делать export предсказаний без shuffle и без ручного копирования логики из train/test loaders.
- `ML/export_entry_path_predictions.py`
  Назначение: единый export `entry_path_v1` предсказаний на `train/validation/test` с колонками модели и контекста сделки (`ATR`, `baseline_score`, `year`).
- `tests/test_entry_path_export_predictions.py`
  Назначение: unit/smoke тесты нового export-пути и контекстных колонок.
- `ML/entry_path_adaptive_conformal.py`
  Назначение: подготовка признаков для модели ошибки, обучение `LightGBMRegressor`, перевод `pred_log_abs_error -> pred_abs_error`, adaptive conformal и оценка правил.
- `ML/benchmark_entry_path_adaptive_conformal.py`
  Назначение: полный benchmark на `validation/test` поверх замороженного `A @ 7.5%`, выпуск JSON/CSV/Markdown артефактов.
- `tests/test_entry_path_adaptive_conformal.py`
  Назначение: unit/smoke тесты adaptive conformal, сетки правил и benchmark CLI.

---

### Task 1: Добавить ordered export для `entry_path_v1` на `train/validation/test`

**Files:**
- Modify: `ML/data_loader.py`
- Create: `ML/export_entry_path_predictions.py`
- Create: `tests/test_entry_path_export_predictions.py`

- [ ] **Step 1: Write the failing tests for context columns and split-path export**

```python
# tests/test_entry_path_export_predictions.py
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, '.')

from ML import export_entry_path_predictions as export_mod


def test_attach_context_columns_adds_atr_year_and_baseline_score():
    export = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2026.02.01 01:00'],
            'signal': [1, -1],
            'pred_ret_24_dir_atr': [0.4, -0.2],
        }
    )
    source = pd.DataFrame(
        {
            'time': ['2025.01.01 00:00', '2026.02.01 01:00'],
            'ATR': [1.5, 2.5],
        }
    )

    enriched = export_mod.attach_context_columns(export, source)

    assert enriched['ATR'].tolist() == [1.5, 2.5]
    assert enriched['baseline_score'].tolist() == [0.4, -0.2]
    assert enriched['year'].tolist() == [2025, 2026]


def test_split_output_path_uses_expected_names(tmp_path: Path):
    assert export_mod.split_output_path(tmp_path, 'train').name == 'entry_path_v1_train_predictions.csv'
    assert export_mod.split_output_path(tmp_path, 'validation').name == 'entry_path_v1_validation_predictions.csv'
    assert export_mod.split_output_path(tmp_path, 'test').name == 'entry_path_test_predictions.csv'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_export_predictions.py -q`
Expected: FAIL with `ImportError` because `export_entry_path_predictions` does not exist.

- [ ] **Step 3: Add ordered split loader helper in `data_loader.py`**

```python
# ML/data_loader.py
def create_data_loaders(
    batch_size: int = 256,
    num_workers: int = 0,
    target: str = 'signal',
    use_scaler: bool = False,
    use_weighted_sampler: bool = False,
    seq_len: int = 100,
    clear_cache: bool = False,
    shuffle_train: bool = True,
) -> tuple[DataLoader, DataLoader, StandardScaler | None]:
    ...
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=shuffle_train,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        drop_last=False,
    )


SPLIT_FILES = {
    'train': TRAIN_FILE,
    'validation': VAL_FILE,
    'test': TEST_FILE,
}


def split_file(split: str) -> Path:
    try:
        return SPLIT_FILES[split]
    except KeyError as exc:
        raise ValueError(f'Unsupported split: {split}') from exc


def create_split_loader(
    split: str,
    batch_size: int = 256,
    target: str = 'predict',
    seq_len: int = 100,
    clear_cache: bool = False,
    num_workers: int = 0,
) -> DataLoader:
    if split == 'test':
        return create_test_loader(
            batch_size=batch_size,
            target=target,
            seq_len=seq_len,
            clear_cache=clear_cache,
            num_workers=num_workers,
        )

    train_loader, val_loader, _ = create_data_loaders(
        batch_size=batch_size,
        num_workers=num_workers,
        target=target,
        use_scaler=False,
        shuffle_train=False,
        seq_len=seq_len,
        clear_cache=clear_cache,
    )
    return train_loader if split == 'train' else val_loader
```

- [ ] **Step 4: Create export module for `train/validation/test`**

```python
# ML/export_entry_path_predictions.py
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ML.data_loader import CSV_SEP, ENTRY_PATH_TARGET, create_split_loader, split_file
from ML.entry_path_task import build_entry_path_export_frame
from ML.evaluate_test import build_entry_path_model


def split_output_path(output_dir: Path, split: str) -> Path:
    names = {
        'train': 'entry_path_v1_train_predictions.csv',
        'validation': 'entry_path_v1_validation_predictions.csv',
        'test': 'entry_path_test_predictions.csv',
    }
    return output_dir / names[split]


def attach_context_columns(export: pd.DataFrame, source_frame: pd.DataFrame) -> pd.DataFrame:
    enriched = export.copy()
    enriched['ATR'] = source_frame['ATR'].to_numpy(dtype=np.float64)
    enriched['baseline_score'] = enriched['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64)
    enriched['year'] = pd.to_datetime(enriched['time'], format='%Y.%m.%d %H:%M', errors='coerce').dt.year.astype('Int64')
    return enriched
```

- [ ] **Step 5: Extend the module with split export run-path**

```python
# ML/export_entry_path_predictions.py
def run_export_for_split(model, device, split: str, output_dir: Path, seq_len: int = 20) -> Path:
    loader = create_split_loader(
        split=split,
        target=ENTRY_PATH_TARGET,
        batch_size=256,
        seq_len=seq_len,
        num_workers=0,
    )
    source = pd.read_csv(split_file(split), sep=CSV_SEP, low_memory=False)

    all_ret = []
    all_path_reg = []
    all_path_cls = []
    all_true_reg = []
    all_true_cls = []
    all_signal = []

    with torch.no_grad():
        for X_batch, y_reg_batch, y_cls_batch, mask_batch, signal_batch in loader:
            outputs = model(X_batch.to(device), mask=mask_batch.to(device))
            all_ret.append(outputs['ret'].cpu().numpy())
            all_path_reg.append(outputs['path_reg'].cpu().numpy())
            all_path_cls.append(torch.softmax(outputs['path_cls'], dim=1).cpu().numpy())
            all_true_reg.append(y_reg_batch.numpy())
            all_true_cls.append(y_cls_batch.numpy())
            all_signal.append(signal_batch.numpy())

    export = build_entry_path_export_frame(
        times=source['time'].to_numpy(),
        signals=np.concatenate(all_signal).astype(int),
        pred_ret=np.concatenate(all_ret),
        pred_path_reg=np.concatenate(all_path_reg),
        pred_path_cls=np.concatenate(all_path_cls),
        true_reg=np.concatenate(all_true_reg),
        true_cls=np.concatenate(all_true_cls),
    )
    export = attach_context_columns(export, source)
    path = split_output_path(output_dir, split)
    export.to_csv(path, sep=';', index=False)
    return path
```

- [ ] **Step 6: Add checkpoint loading and CLI entrypoint**

```python
# ML/export_entry_path_predictions.py
def run_export(checkpoint_path, splits, output_dir):
    ckpt = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
    model = build_entry_path_model(ckpt.get('model_kwargs', {}))
    model.load_state_dict(ckpt['model_state_dict'])
    model.eval()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for split in splits:
        run_export_for_split(model, torch.device('cpu'), split, output_dir)


def parse_args():
    parser = argparse.ArgumentParser(description='Export entry_path_v1 predictions for train/validation/test splits.')
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--splits', nargs='+', default=['validation', 'test'])
    parser.add_argument('--output-dir', default='ML/reports')
    return parser.parse_args()


def main():
    args = parse_args()
    run_export(args.checkpoint, args.splits, args.output_dir)


if __name__ == '__main__':
    main()
```

- [ ] **Step 7: Run focused tests to verify the export helpers pass**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_export_predictions.py -q`
Expected: PASS for 2 tests.

- [ ] **Step 8: Commit**

```bash
git add ML/data_loader.py ML/export_entry_path_predictions.py tests/test_entry_path_export_predictions.py
git commit -m "feat: add ordered entry path prediction export"
```

---

### Task 2: Добавить ядро adaptive conformal и модель ошибки

**Files:**
- Create: `ML/entry_path_adaptive_conformal.py`
- Create: `tests/test_entry_path_adaptive_conformal.py`

- [ ] **Step 1: Write the failing tests for target transform, inverse transform, and adaptive interval**

```python
# tests/test_entry_path_adaptive_conformal.py
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, '.')

from ML import entry_path_adaptive_conformal as epac


def test_log_abs_error_transform_round_trips():
    err = np.array([0.0, 0.5, 2.0], dtype=np.float64)
    transformed = epac.to_log_abs_error(err)
    restored = epac.from_log_abs_error(transformed)
    assert np.allclose(restored, err)


def test_build_error_features_uses_prediction_columns_and_context():
    frame = pd.DataFrame(
        {
            'pred_ret_6_dir_atr': [0.1],
            'pred_ret_12_dir_atr': [0.2],
            'pred_ret_24_dir_atr': [0.3],
            'pred_fav_6_atr': [0.4],
            'pred_adv_6_atr': [0.5],
            'pred_fav_12_atr': [0.6],
            'pred_adv_12_atr': [0.7],
            'pred_fav_24_atr': [0.8],
            'pred_adv_24_atr': [0.9],
            'pred_path_6_prob_neg': [0.2],
            'pred_path_6_prob_flat': [0.3],
            'pred_path_6_prob_pos': [0.5],
            'signal': [1],
            'ATR': [1.7],
            'baseline_score': [0.3],
            'year': [2025],
        }
    )

    X = epac.build_error_features(frame)

    assert X.shape == (1, len(epac.ERROR_FEATURE_COLUMNS))
    assert list(X.columns) == epac.ERROR_FEATURE_COLUMNS


def test_build_adaptive_interval_uses_scaled_error():
    lower, upper, width = epac.build_adaptive_interval(
        prediction=np.array([1.0, 0.5], dtype=np.float64),
        pred_abs_error=np.array([0.2, 0.4], dtype=np.float64),
        quantile=2.0,
    )

    assert np.allclose(lower, np.array([0.6, -0.3]))
    assert np.allclose(upper, np.array([1.4, 1.3]))
    assert np.allclose(width, np.array([0.8, 1.6]))


def test_compute_normalized_quantile_divides_by_predicted_error():
    q = epac.compute_normalized_quantile(
        y_true=np.array([1.0, 2.0], dtype=np.float64),
        y_pred=np.array([0.8, 1.0], dtype=np.float64),
        pred_abs_error=np.array([0.2, 0.5], dtype=np.float64),
        alpha=0.10,
    )

    assert q == pytest.approx(2.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_adaptive_conformal.py -q`
Expected: FAIL with `ImportError` because `entry_path_adaptive_conformal` does not exist.

- [ ] **Step 3: Implement the adaptive conformal core with LightGBM error model**

```python
# ML/entry_path_adaptive_conformal.py
import numpy as np
import pandas as pd
import lightgbm as lgb


ERROR_FEATURE_COLUMNS = [
    'pred_ret_6_dir_atr',
    'pred_ret_12_dir_atr',
    'pred_ret_24_dir_atr',
    'pred_fav_6_atr', 'pred_adv_6_atr',
    'pred_fav_12_atr', 'pred_adv_12_atr',
    'pred_fav_24_atr', 'pred_adv_24_atr',
    'pred_path_6_prob_neg', 'pred_path_6_prob_flat', 'pred_path_6_prob_pos',
    'signal', 'ATR', 'baseline_score', 'year',
]


def to_log_abs_error(abs_error) -> np.ndarray:
    abs_error = np.asarray(abs_error, dtype=np.float64)
    return np.log1p(abs_error)


def from_log_abs_error(log_abs_error) -> np.ndarray:
    return np.expm1(np.asarray(log_abs_error, dtype=np.float64))


def build_error_features(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[ERROR_FEATURE_COLUMNS].copy()


def fit_error_model(train_frame: pd.DataFrame) -> lgb.LGBMRegressor:
    abs_error = np.abs(
        train_frame['true_ret_24_dir_atr'].to_numpy(dtype=np.float64)
        - train_frame['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64)
    )
    target = to_log_abs_error(abs_error)
    X = build_error_features(train_frame)
    model = lgb.LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        random_state=42,
    )
    model.fit(X, target)
    return model


def predict_abs_error(model, frame: pd.DataFrame) -> np.ndarray:
    pred_log = model.predict(build_error_features(frame))
    pred_abs = from_log_abs_error(pred_log)
    return np.clip(pred_abs, 1e-6, None)
```

- [ ] **Step 4: Extend the module with normalized residuals and rule helpers**

```python
# ML/entry_path_adaptive_conformal.py
def compute_normalized_quantile(y_true, y_pred, pred_abs_error, alpha: float = 0.10) -> float:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    pred_abs_error = np.asarray(pred_abs_error, dtype=np.float64)
    score = np.abs(y_true - y_pred) / np.clip(pred_abs_error, 1e-6, None)
    level = min((1.0 - alpha) * (1.0 + 1.0 / len(score)), 1.0)
    return float(np.quantile(score, level))


def build_adaptive_interval(prediction, pred_abs_error, quantile: float):
    prediction = np.asarray(prediction, dtype=np.float64)
    pred_abs_error = np.asarray(pred_abs_error, dtype=np.float64)
    radius = float(quantile) * pred_abs_error
    lower = prediction - radius
    upper = prediction + radius
    width = 2.0 * radius
    return lower, upper, width


def apply_lb_rule(lower_bound, margin: float) -> np.ndarray:
    return np.asarray(lower_bound, dtype=np.float64) > float(margin)


def apply_width_rule(width, max_width: float) -> np.ndarray:
    return np.asarray(width, dtype=np.float64) <= float(max_width)
```

- [ ] **Step 5: Run focused tests to verify the adaptive core passes**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_adaptive_conformal.py -q`
Expected: PASS for 4 tests.

- [ ] **Step 6: Commit**

```bash
git add ML/entry_path_adaptive_conformal.py tests/test_entry_path_adaptive_conformal.py
git commit -m "feat: add adaptive conformal core"
```

---

### Task 3: Добавить benchmark adaptive conformal и сетку правил

**Files:**
- Modify: `ML/entry_path_adaptive_conformal.py`
- Create: `ML/benchmark_entry_path_adaptive_conformal.py`
- Modify: `tests/test_entry_path_adaptive_conformal.py`

- [ ] **Step 1: Add failing tests for candidate grid and benchmark artifact writing**

```python
def test_evaluate_candidate_grid_includes_lb_and_width_rules():
    frame = pd.DataFrame(
        {
            'time': pd.to_datetime(['2023-01-01 00:00', '2023-01-02 00:00', '2024-01-01 00:00', '2024-01-02 00:00']),
            'signal': [1, 1, -1, -1],
            'pred_ret_24_dir_atr': [1.2, 0.6, 0.4, 0.2],
            'true_ret_24_dir_atr': [1.5, 0.1, -0.2, -0.4],
        }
    )
    pred_abs_error = np.array([0.2, 0.3, 0.4, 0.5], dtype=np.float64)

    table = epac.evaluate_candidate_grid(
        frame=frame,
        pred_abs_error=pred_abs_error,
        quantile=2.0,
        lb_margins=(0.0, 0.25),
        width_caps=(1.0,),
        min_period_trades=1,
        hold_bars=24,
    )

    assert 'baseline' in table['candidate'].tolist()
    assert 'LB>0' in table['candidate'].tolist()
    assert 'LB>0.25|W<=1' in table['candidate'].tolist()


def test_run_benchmark_writes_adaptive_artifacts(tmp_path: Path):
    train = pd.DataFrame(
        {
            'time': ['2020.01.01 00:00', '2020.01.02 00:00'],
            'signal': [1, -1],
            'ATR': [1.0, 1.2],
            'baseline_score': [0.4, -0.1],
            'year': [2020, 2020],
            'pred_ret_6_dir_atr': [0.2, -0.1],
            'pred_ret_12_dir_atr': [0.3, -0.2],
            'pred_ret_24_dir_atr': [0.4, -0.3],
            'pred_fav_6_atr': [0.5, 0.4], 'pred_adv_6_atr': [0.1, 0.2],
            'pred_fav_12_atr': [0.6, 0.5], 'pred_adv_12_atr': [0.1, 0.2],
            'pred_fav_24_atr': [0.7, 0.6], 'pred_adv_24_atr': [0.1, 0.2],
            'pred_path_6_prob_neg': [0.2, 0.5],
            'pred_path_6_prob_flat': [0.3, 0.3],
            'pred_path_6_prob_pos': [0.5, 0.2],
            'true_ret_24_dir_atr': [0.7, -0.1],
        }
    )
    validation = train.copy()
    test = train.copy()
    train_path = tmp_path / 'train.csv'
    val_path = tmp_path / 'val.csv'
    test_path = tmp_path / 'test.csv'
    train.to_csv(train_path, sep=';', index=False)
    validation.to_csv(val_path, sep=';', index=False)
    test.to_csv(test_path, sep=';', index=False)

    baseline_rule = tmp_path / 'baseline.json'
    baseline_rule.write_text(json.dumps({'winner': {'candidate': 'A', 'score_threshold': -999.0}}), encoding='utf-8')

    payload = bench.run_benchmark(
        train_csv=train_path,
        validation_csv=val_path,
        test_csv=test_path,
        baseline_rule_path=baseline_rule,
        output_dir=tmp_path,
        alpha=0.10,
        min_trades=1,
    )

    assert (tmp_path / 'entry_path_adaptive_conformal_selected_rule.json').exists()
    assert (tmp_path / 'entry_path_adaptive_conformal_report.md').exists()
    assert payload['winner']['candidate']
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_adaptive_conformal.py -q`
Expected: FAIL with missing `evaluate_candidate_grid` and `benchmark_entry_path_adaptive_conformal`.

- [ ] **Step 3: Implement candidate evaluation and rule selection**

```python
# ML/entry_path_adaptive_conformal.py
from ML.entry_path_trade_filter import evaluate_frozen_threshold
from ML.entry_path_trade_filter import run_sequential_check


def evaluate_candidate_grid(
    frame: pd.DataFrame,
    pred_abs_error,
    quantile: float,
    lb_margins=(0.0, 0.25, 0.5),
    width_caps=(1.0, 1.5, 2.0),
    min_period_trades: int = 10,
    hold_bars: int = 24,
) -> pd.DataFrame:
    prediction = frame['pred_ret_24_dir_atr'].to_numpy(dtype=np.float64)
    lower, _upper, width = build_adaptive_interval(prediction, pred_abs_error, quantile)
    rows = []

    baseline = evaluate_frozen_threshold(
        frame=frame,
        score=np.ones(len(frame), dtype=np.float64),
        candidate='baseline',
        threshold=float('-inf'),
        target_coverage=1.0,
        min_period_trades=min_period_trades,
    ).iloc[0].to_dict()
    baseline_seq = run_sequential_check(frame, np.ones(len(frame), dtype=bool), hold_bars=hold_bars)
    baseline.update({'quantile': float(quantile), 'sequential_pf': float(baseline_seq['pf'])})
    rows.append(baseline)

    for margin in lb_margins:
        lb_mask = apply_lb_rule(lower, margin)
        row = evaluate_frozen_threshold(
            frame=frame,
            score=lower,
            candidate=f'LB>{margin:g}',
            threshold=float(margin),
            target_coverage=np.nan,
            min_period_trades=min_period_trades,
        ).iloc[0].to_dict()
        row.update({'quantile': float(quantile), 'margin': float(margin), 'width_cap': np.nan, 'sequential_pf': float(run_sequential_check(frame, lb_mask, hold_bars=hold_bars)['pf'])})
        rows.append(row)

        for width_cap in width_caps:
            mask = lb_mask & apply_width_rule(width, width_cap)
            candidate_name = f'LB>{margin:g}|W<={width_cap:g}'
            row = evaluate_frozen_threshold(
                frame=frame,
                score=np.where(mask, 1.0, -1.0),
                candidate=candidate_name,
                threshold=0.0,
                target_coverage=np.nan,
                min_period_trades=min_period_trades,
            ).iloc[0].to_dict()
            row.update({'quantile': float(quantile), 'margin': float(margin), 'width_cap': float(width_cap), 'sequential_pf': float(run_sequential_check(frame, mask, hold_bars=hold_bars)['pf'])})
            rows.append(row)

    return pd.DataFrame(rows)


def pick_best_adaptive_candidate(table: pd.DataFrame, min_trades: int = 25) -> pd.Series:
    baseline_row = table.loc[table['candidate'] == 'baseline'].iloc[0]
    eligible = table.loc[
        (table['candidate'] != 'baseline')
        & (table['trades'] >= int(min_trades))
        & (table['sequential_pf'] >= float(baseline_row['sequential_pf']))
    ].copy()
    if eligible.empty:
        return baseline_row
    return eligible.sort_values(
        ['pf', 'mean_pnl_atr', 'stability_ratio', 'trades'],
        ascending=[False, False, False, False],
    ).iloc[0]
```

- [ ] **Step 4: Add benchmark CLI and report writer**

```python
# ML/benchmark_entry_path_adaptive_conformal.py
import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from ML.entry_path_adaptive_conformal import compute_normalized_quantile
from ML.entry_path_adaptive_conformal import evaluate_candidate_grid
from ML.entry_path_adaptive_conformal import fit_error_model
from ML.entry_path_adaptive_conformal import pick_best_adaptive_candidate
from ML.entry_path_adaptive_conformal import predict_abs_error


def run_benchmark(
    train_csv,
    validation_csv,
    test_csv,
    baseline_rule_path,
    output_dir,
    alpha=0.10,
    min_trades=25,
    lb_margins=(0.0, 0.25, 0.5),
    width_caps=(1.0, 1.5, 2.0),
    min_period_trades=10,
    sequential_hold_bars=24,
):
    train_frame = pd.read_csv(train_csv, sep=';')
    validation_frame = pd.read_csv(validation_csv, sep=';')
    test_frame = pd.read_csv(test_csv, sep=';')
    baseline_rule = json.loads(Path(baseline_rule_path).read_text(encoding='utf-8'))

    from ML.entry_path_conformal_filter import apply_baseline_rule
    validation_frame, _ = apply_baseline_rule(validation_frame, baseline_rule)
    test_frame, _ = apply_baseline_rule(test_frame, baseline_rule)

    error_model = fit_error_model(train_frame.loc[train_frame['signal'] != 0].copy())
    val_pred_abs_error = predict_abs_error(error_model, validation_frame)
    quantile = compute_normalized_quantile(
        y_true=validation_frame['true_ret_24_dir_atr'].to_numpy(dtype='float64'),
        y_pred=validation_frame['pred_ret_24_dir_atr'].to_numpy(dtype='float64'),
        pred_abs_error=val_pred_abs_error,
        alpha=alpha,
    )
```

- [ ] **Step 5: Finish the CLI by writing artifacts**

```python
# ML/benchmark_entry_path_adaptive_conformal.py
    validation_summary = evaluate_candidate_grid(
        frame=validation_frame,
        pred_abs_error=val_pred_abs_error,
        quantile=quantile,
        lb_margins=lb_margins,
        width_caps=width_caps,
        min_period_trades=min_period_trades,
        hold_bars=sequential_hold_bars,
    )
    winner = pick_best_adaptive_candidate(validation_summary, min_trades=min_trades)

    test_pred_abs_error = predict_abs_error(error_model, test_frame)
    test_summary = evaluate_candidate_grid(
        frame=test_frame,
        pred_abs_error=test_pred_abs_error,
        quantile=quantile,
        lb_margins=(),
        width_caps=(),
        min_period_trades=min_period_trades,
        hold_bars=sequential_hold_bars,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / 'entry_path_error_lgbm.joblib'
    validation_path = output_dir / 'entry_path_adaptive_conformal_validation_summary.csv'
    test_path = output_dir / 'entry_path_adaptive_conformal_test_summary.csv'
    rule_path = output_dir / 'entry_path_adaptive_conformal_selected_rule.json'
    report_path = output_dir / 'entry_path_adaptive_conformal_report.md'

    joblib.dump(error_model, model_path)
    validation_summary.to_csv(validation_path, sep=';', index=False)
    test_summary.to_csv(test_path, sep=';', index=False)

    payload = {
        'train_csv': str(train_csv),
        'validation_csv': str(validation_csv),
        'test_csv': str(test_csv),
        'baseline_rule_path': str(baseline_rule_path),
        'alpha': float(alpha),
        'quantile': float(quantile),
        'winner': winner.to_dict(),
        'error_model_path': str(model_path),
    }
    rule_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    report_path.write_text(
        '# Entry Path Adaptive Conformal Report\\n\\n'
        f'- winner: `{winner[\"candidate\"]}`\\n'
        f'- validation_pf: **{float(winner[\"pf\"]):.4f}**\\n'
        f'- quantile: **{float(quantile):.4f}**\\n',
        encoding='utf-8',
    )
    return payload
```

- [ ] **Step 6: Add CLI entrypoint for the adaptive benchmark**

```python
# ML/benchmark_entry_path_adaptive_conformal.py
def parse_args():
    parser = argparse.ArgumentParser(description='Benchmark adaptive conformal on frozen entry_path_v1 predictions.')
    parser.add_argument('--train-csv', required=True)
    parser.add_argument('--validation-csv', required=True)
    parser.add_argument('--test-csv', required=True)
    parser.add_argument('--baseline-rule-path', required=True)
    parser.add_argument('--output-dir', default='ML/reports')
    parser.add_argument('--alpha', type=float, default=0.10)
    parser.add_argument('--lb-margins', nargs='+', type=float, default=[0.0, 0.25, 0.5])
    parser.add_argument('--width-caps', nargs='+', type=float, default=[1.0, 1.5, 2.0])
    parser.add_argument('--min-trades', type=int, default=25)
    parser.add_argument('--min-period-trades', type=int, default=10)
    parser.add_argument('--sequential-hold-bars', type=int, default=24)
    return parser.parse_args()


def main():
    args = parse_args()
    payload = run_benchmark(
        train_csv=args.train_csv,
        validation_csv=args.validation_csv,
        test_csv=args.test_csv,
        baseline_rule_path=args.baseline_rule_path,
        output_dir=args.output_dir,
        alpha=args.alpha,
        min_trades=args.min_trades,
        lb_margins=tuple(args.lb_margins),
        width_caps=tuple(args.width_caps),
        min_period_trades=args.min_period_trades,
        sequential_hold_bars=args.sequential_hold_bars,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
```

- [ ] **Step 7: Run the adaptive conformal test suite**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_adaptive_conformal.py tests/test_entry_path_export_predictions.py -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add ML/entry_path_adaptive_conformal.py ML/benchmark_entry_path_adaptive_conformal.py tests/test_entry_path_adaptive_conformal.py
git commit -m "feat: add adaptive conformal benchmark"
```

---

### Task 4: Выпустить реальные adaptive артефакты и проверить победителя

**Files:**
- Modify: `ML/reports/entry_path_v1_train_predictions.csv`
- Modify: `ML/reports/entry_path_v1_validation_predictions.csv`
- Modify: `ML/reports/entry_path_test_predictions.csv`
- Modify: `ML/reports/entry_path_adaptive_conformal_selected_rule.json`
- Modify: `ML/reports/entry_path_adaptive_conformal_report.md`
- Modify: `ML/reports/entry_path_adaptive_conformal_validation_summary.csv`
- Modify: `ML/reports/entry_path_adaptive_conformal_test_summary.csv`

- [ ] **Step 1: Export `train/validation/test` predictions for the frozen `entry_path_v1` checkpoint**

Run:

```bash
./.venv/bin/python -m ML.export_entry_path_predictions \
  --checkpoint ML/checkpoints/transformer_entry_path_v1_best.pt \
  --splits train validation test \
  --output-dir ML/reports
```

Expected: three CSV files written:
- `ML/reports/entry_path_v1_train_predictions.csv`
- `ML/reports/entry_path_v1_validation_predictions.csv`
- `ML/reports/entry_path_test_predictions.csv`

- [ ] **Step 2: Run the adaptive benchmark on the frozen `A @ 7.5%` base**

Run:

```bash
./.venv/bin/python -m ML.benchmark_entry_path_adaptive_conformal \
  --train-csv ML/reports/entry_path_v1_train_predictions.csv \
  --validation-csv ML/reports/entry_path_v1_validation_predictions.csv \
  --test-csv ML/reports/entry_path_test_predictions.csv \
  --baseline-rule-path ML/reports/entry_path_trade_filter_selected_rule.json \
  --output-dir ML/reports \
  --alpha 0.10 \
  --lb-margins 0.0 0.25 0.5 \
  --width-caps 1.0 1.5 2.0 \
  --min-trades 25 \
  --min-period-trades 10 \
  --sequential-hold-bars 24
```

Expected: JSON payload printed and adaptive artifacts written under `ML/reports/`.

- [ ] **Step 3: Verify the winner is frozen from validation and sequential check did not regress**

Run:

```bash
./.venv/bin/python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path('ML/reports/entry_path_adaptive_conformal_selected_rule.json').read_text(encoding='utf-8'))
winner = payload['winner']
assert winner['candidate']
assert int(winner['trades']) >= 25 or winner['candidate'] == 'baseline'
print(winner['candidate'], winner['trades'], winner['pf'])
PY
```

Expected: one short line like `LB>0.25|W<=1.5 29 3.1142` or `baseline 36 2.6684`.

- [ ] **Step 4: Re-run focused tests after the real artifact pass**

Run: `./.venv/bin/python -m pytest tests/test_entry_path_export_predictions.py tests/test_entry_path_adaptive_conformal.py tests/test_entry_path_trade_filter.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ML/reports/entry_path_v1_train_predictions.csv ML/reports/entry_path_v1_validation_predictions.csv ML/reports/entry_path_test_predictions.csv ML/reports/entry_path_adaptive_conformal_selected_rule.json ML/reports/entry_path_adaptive_conformal_report.md ML/reports/entry_path_adaptive_conformal_validation_summary.csv ML/reports/entry_path_adaptive_conformal_test_summary.csv
git commit -m "chore: publish adaptive conformal artifacts"
```
