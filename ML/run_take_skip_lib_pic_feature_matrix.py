# =============================================================================
# Файл: run_take_skip_lib_pic_feature_matrix.py
# Назначение: Bounded training matrix для take_skip_v2 с lib_PIC feature profiles.
# Обновлён: 2026-04-20
# Входные данные:
#   - DATA/Nero_train_labeled.csv
#   - DATA/Nero_validation_labeled.csv
#   - DATA/Nero_test_labeled.csv
# Выходные данные:
#   - ML/reports/take_skip_lib_pic_feature_matrix/
# Использование:
#   python -m ML.run_take_skip_lib_pic_feature_matrix --feature-profiles baseline_clean --seq-lens 20 --jobs 1
# Примечания:
#   - Это отдельный research runner; общий ML.train не меняется.
#   - Если --target-columns не задан, используются только цели, присутствующие в CSV.
# =============================================================================

from __future__ import annotations

import argparse
import contextlib
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from ML.benchmark_take_skip_trailing_stop_v2 import run_benchmark
from ML.data_loader import (
    N_FRACTAL_FEATURES,
    TEST_FILE,
    TRAIN_FILE,
    VAL_FILE,
    parse_fractals_to_3d,
)
from ML.lib_pic_feature_profiles import build_lib_pic_feature_profile
from ML.models.take_skip_dual_stream_transformer import TakeSkipDualStreamTransformer
from ML.take_skip_trailing_stop_v2_task import (
    TAKE_SKIP_THRESHOLD_ATR_V2,
    TAKE_SKIP_TRAILING_STOP_V2_COLUMNS,
    TAKE_SKIP_TRAILING_STOP_V2_TARGET,
)
from ML.utils import get_device, set_seed


DEFAULT_FEATURE_PROFILES = ('baseline_clean', 'baseline_clean_path', 'baseline_clean_geometry_path')
DEFAULT_SEQ_LENS = (20, 50, 100)
DEFAULT_TARGET_COLUMNS = tuple(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS)
AUTO_VALUE = 'auto'


@dataclass(frozen=True)
class TakeSkipFeatureArrays:
    X: np.ndarray
    mask: np.ndarray
    engineered: np.ndarray
    y: np.ndarray
    signal: np.ndarray
    times: np.ndarray
    true_pnl: np.ndarray


def target_to_true_pnl_column(target_column: str) -> str:
    _, horizon, x_suffix = target_column.split('_')
    return f'trail_{horizon}_pnl_atr_{x_suffix}'


def resolve_target_columns(frame: pd.DataFrame, requested: tuple[str, ...] | None = None) -> tuple[str, ...]:
    if requested is not None:
        missing = [target for target in requested if target_to_true_pnl_column(target) not in frame.columns]
        if missing:
            raise ValueError(f'missing requested take/skip v2 source columns: {missing}')
        return tuple(requested)

    available = tuple(
        target
        for target in DEFAULT_TARGET_COLUMNS
        if target_to_true_pnl_column(target) in frame.columns
    )
    if not available:
        raise ValueError('no take/skip v2 source columns found')
    return available


def _split_targets(frame: pd.DataFrame, target_columns: tuple[str, ...]) -> np.ndarray:
    source_columns = [target_to_true_pnl_column(target) for target in target_columns]
    missing = [column for column in source_columns if column not in frame.columns]
    if missing:
        raise ValueError(f'missing take/skip v2 source columns: {missing}')
    pnl = frame[source_columns].to_numpy(dtype=np.float32)
    return (pnl >= TAKE_SKIP_THRESHOLD_ATR_V2).astype(np.float32)


def _compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, target_columns: tuple[str, ...]) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=np.float32)
    y_prob = np.asarray(y_prob, dtype=np.float32)
    if y_true.shape != y_prob.shape:
        raise ValueError(f'y_true shape {y_true.shape} does not match y_prob shape {y_prob.shape}')
    if y_true.ndim != 2 or y_true.shape[1] != len(target_columns):
        raise ValueError(f'y_true must have shape (n, {len(target_columns)})')
    if not np.isfinite(y_true).all() or not np.isfinite(y_prob).all():
        raise ValueError('non-finite values are not allowed in y_true or y_prob')
    if not np.isin(y_true, (0.0, 1.0)).all():
        raise ValueError('y_true must contain only 0/1 labels')
    if (y_prob < 0.0).any() or (y_prob > 1.0).any():
        raise ValueError('y_prob must contain probabilities in [0, 1]')

    clipped = np.clip(y_prob, 1e-7, 1.0 - 1e-7)
    bce = -(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped))
    metrics: dict[str, float] = {'bce': float(np.mean(bce))}
    for idx, target in enumerate(target_columns):
        yt = y_true[:, idx]
        yp = y_prob[:, idx]
        metrics[f'positive_rate_{target}'] = float(np.mean(yt))
        metrics[f'brier_{target}'] = float(np.mean((yp - yt) ** 2))
    return metrics


class TakeSkipFeatureDataset(Dataset):
    """Dataset для dual-stream take_skip_v2: sequence + engineered features + labels."""

    def __init__(self, arrays: TakeSkipFeatureArrays):
        self.X = torch.from_numpy(arrays.X.astype(np.float32)).float()
        self.mask = torch.from_numpy(arrays.mask.astype(bool)).bool()
        self.engineered = torch.from_numpy(arrays.engineered.astype(np.float32)).float()
        self.y = torch.from_numpy(arrays.y.astype(np.float32)).float()

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int):
        return self.X[idx], self.engineered[idx], self.y[idx], self.mask[idx]


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, 'tolist'):
        return _json_safe(value.tolist())
    if hasattr(value, 'item'):
        return _json_safe(value.item())
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return 'inf' if value > 0 else '-inf'
    return value


def config_slug(feature_profile: str, seq_len: int) -> str:
    return f'{feature_profile}_seq{seq_len}'


def _parse_auto_int(value: int | str | None, *, name: str) -> int | str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.lower() == AUTO_VALUE:
        return AUTO_VALUE
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{name} must be a positive integer or "auto"') from exc
    if parsed < 1:
        raise ValueError(f'{name} must be >= 1')
    return parsed


def resolve_cpu_schedule(
    *,
    config_count: int,
    jobs: int | str = AUTO_VALUE,
    torch_threads: int | str | None = AUTO_VALUE,
    cpu_load: float = 0.5,
    cpu_count: int | None = None,
) -> dict[str, int | float]:
    if config_count < 1:
        raise ValueError('config_count must be >= 1')
    if not 0.0 < cpu_load <= 1.0:
        raise ValueError('cpu_load must be in (0.0, 1.0]')

    detected_cpu = int(cpu_count or os.cpu_count() or 1)
    target_threads = max(1, int(math.floor(detected_cpu * cpu_load)))
    parsed_jobs = _parse_auto_int(jobs, name='jobs')
    parsed_torch_threads = _parse_auto_int(torch_threads, name='torch_threads')

    default_threads_per_job = 4
    if parsed_jobs == AUTO_VALUE and (parsed_torch_threads == AUTO_VALUE or parsed_torch_threads is None):
        resolved_jobs = min(config_count, max(1, target_threads // default_threads_per_job))
        resolved_torch_threads = max(1, target_threads // resolved_jobs)
    elif parsed_jobs == AUTO_VALUE:
        resolved_torch_threads = int(parsed_torch_threads)
        resolved_jobs = min(config_count, max(1, target_threads // resolved_torch_threads))
    elif parsed_torch_threads == AUTO_VALUE or parsed_torch_threads is None:
        resolved_jobs = min(config_count, int(parsed_jobs))
        resolved_torch_threads = max(1, target_threads // resolved_jobs)
    else:
        resolved_jobs = min(config_count, int(parsed_jobs))
        resolved_torch_threads = int(parsed_torch_threads)

    return {
        'cpu_count': detected_cpu,
        'cpu_load': float(cpu_load),
        'target_threads': target_threads,
        'jobs': resolved_jobs,
        'torch_threads': resolved_torch_threads,
    }


def build_take_skip_feature_arrays(
    frame: pd.DataFrame,
    *,
    feature_profile: str,
    seq_len: int,
    target_columns: tuple[str, ...] | None = None,
) -> TakeSkipFeatureArrays:
    target_columns = resolve_target_columns(frame, target_columns)
    X, mask = parse_fractals_to_3d(frame)
    seq_len = int(seq_len)
    if not 1 <= seq_len <= X.shape[1]:
        raise ValueError(f'seq_len must be in [1, {X.shape[1]}], got {seq_len}')
    X = X[:, :seq_len, :]
    mask = mask[:, :seq_len]

    engineered = build_lib_pic_feature_profile(frame, profile=feature_profile, seq_len=seq_len).to_numpy(dtype=np.float32)
    engineered = np.nan_to_num(engineered, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    y = _split_targets(frame, target_columns)
    true_pnl = frame[[target_to_true_pnl_column(target) for target in target_columns]].to_numpy(dtype=np.float32)
    signal = pd.to_numeric(frame['signal'], errors='coerce').fillna(0).to_numpy(dtype=np.int64)
    times = frame['time'].astype(str).to_numpy(dtype=object)
    return TakeSkipFeatureArrays(
        X=X.astype(np.float32),
        mask=mask.astype(bool),
        engineered=engineered,
        y=y.astype(np.float32),
        signal=signal,
        times=times,
        true_pnl=true_pnl,
    )


def _read_labeled_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=';', low_memory=False)


def _make_loader(arrays: TakeSkipFeatureArrays, *, batch_size: int, shuffle: bool) -> DataLoader:
    return DataLoader(TakeSkipFeatureDataset(arrays), batch_size=batch_size, shuffle=shuffle, drop_last=False)


def _predict(model: nn.Module, loader: DataLoader, device: torch.device) -> np.ndarray:
    model.eval()
    chunks = []
    with torch.no_grad():
        for X_batch, engineered_batch, _y_batch, mask_batch in loader:
            logits = model(X_batch.to(device), engineered=engineered_batch.to(device), mask=mask_batch.to(device))
            chunks.append(torch.sigmoid(logits).cpu().numpy())
    return np.vstack(chunks).astype(np.float32)


def _train_one_epoch(model: nn.Module, loader: DataLoader, loss_fn: nn.Module, optimizer, device: torch.device) -> float:
    model.train()
    losses = []
    for X_batch, engineered_batch, y_batch, mask_batch in loader:
        optimizer.zero_grad(set_to_none=True)
        logits = model(X_batch.to(device), engineered=engineered_batch.to(device), mask=mask_batch.to(device))
        loss = loss_fn(logits, y_batch.to(device))
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu().item()))
    return float(np.mean(losses)) if losses else 0.0


def _validate(
    model: nn.Module,
    loader: DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
    target_columns: tuple[str, ...],
) -> tuple[float, dict[str, float]]:
    model.eval()
    losses = []
    y_true = []
    y_prob = []
    with torch.no_grad():
        for X_batch, engineered_batch, y_batch, mask_batch in loader:
            logits = model(X_batch.to(device), engineered=engineered_batch.to(device), mask=mask_batch.to(device))
            loss = loss_fn(logits, y_batch.to(device))
            losses.append(float(loss.detach().cpu().item()))
            y_true.append(y_batch.cpu().numpy())
            y_prob.append(torch.sigmoid(logits).cpu().numpy())
    true = np.vstack(y_true).astype(np.float32)
    prob = np.vstack(y_prob).astype(np.float32)
    metrics = _compute_metrics(true, prob, target_columns)
    metrics['val_score'] = -metrics['bce']
    return float(np.mean(losses)) if losses else 0.0, metrics


def _export_predictions(
    path: Path,
    arrays: TakeSkipFeatureArrays,
    pred_prob: np.ndarray,
    target_columns: tuple[str, ...],
) -> None:
    pred_prob = np.asarray(pred_prob, dtype=np.float32)
    if pred_prob.shape != arrays.y.shape:
        raise ValueError(f'pred_prob shape {pred_prob.shape} does not match target shape {arrays.y.shape}')
    frame = pd.DataFrame({'time': arrays.times, 'signal': arrays.signal})
    for idx, target in enumerate(target_columns):
        frame[f'pred_{target}'] = pred_prob[:, idx]
        frame[f'true_{target}'] = arrays.y[:, idx]
        frame[f'true_{target_to_true_pnl_column(target)}'] = arrays.true_pnl[:, idx]
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, sep=';', index=False)


def run_single_config_from_frames(
    *,
    train_frame: pd.DataFrame,
    validation_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
    output_root: Path,
    feature_profile: str,
    seq_len: int,
    epochs: int,
    patience: int,
    batch_size: int,
    seed: int,
    min_pf: float,
    min_trades_per_year: float,
    target_columns: tuple[str, ...] | None = None,
    torch_threads: int | None = None,
    model_kwargs: dict | None = None,
) -> dict[str, object]:
    if torch_threads is not None and torch_threads > 0:
        torch.set_num_threads(int(torch_threads))
    set_seed(seed)
    started_at = time.time()
    run_dir = output_root / config_slug(feature_profile, seq_len)
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f'[start] {run_dir.name}: profile={feature_profile} seq_len={seq_len}', flush=True)

    target_columns = resolve_target_columns(train_frame, target_columns)
    print(f'[targets] {run_dir.name}: {", ".join(target_columns)}', flush=True)
    for split_name, frame in [('validation', validation_frame), ('test', test_frame)]:
        split_targets = resolve_target_columns(frame, target_columns)
        if split_targets != target_columns:
            raise ValueError(f'{split_name} target columns differ from train target columns')

    train_arrays = build_take_skip_feature_arrays(train_frame, feature_profile=feature_profile, seq_len=seq_len, target_columns=target_columns)
    validation_arrays = build_take_skip_feature_arrays(validation_frame, feature_profile=feature_profile, seq_len=seq_len, target_columns=target_columns)
    test_arrays = build_take_skip_feature_arrays(test_frame, feature_profile=feature_profile, seq_len=seq_len, target_columns=target_columns)

    train_loader = _make_loader(train_arrays, batch_size=batch_size, shuffle=True)
    validation_loader = _make_loader(validation_arrays, batch_size=batch_size, shuffle=False)
    test_loader = _make_loader(test_arrays, batch_size=batch_size, shuffle=False)

    kwargs = dict(model_kwargs or {})
    kwargs.setdefault('input_features', N_FRACTAL_FEATURES)
    kwargs.setdefault('engineered_feature_dim', int(train_arrays.engineered.shape[1]))
    kwargs.setdefault('output_dim', len(target_columns))

    device = get_device()
    model = TakeSkipDualStreamTransformer(**kwargs).to(device)
    loss_fn = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    best_score = -float('inf')
    best_epoch = 0
    best_metrics: dict[str, float] = {}
    history = []
    stale_epochs = 0
    checkpoint_path = run_dir / 'checkpoint.pt'

    for epoch in range(1, epochs + 1):
        train_loss = _train_one_epoch(model, train_loader, loss_fn, optimizer, device)
        val_loss, metrics = _validate(model, validation_loader, loss_fn, device, target_columns)
        score = float(metrics['val_score'])
        history.append({'epoch': epoch, 'train_loss': train_loss, 'val_loss': val_loss, **metrics})
        print(
            f'[epoch] {run_dir.name}: {epoch}/{epochs} train_loss={train_loss:.6f} val_loss={val_loss:.6f} bce={metrics["bce"]:.6f}',
            flush=True,
        )
        if score > best_score:
            best_score = score
            best_epoch = epoch
            best_metrics = metrics
            stale_epochs = 0
            torch.save(
                {
                    'model_state_dict': model.state_dict(),
                    'model_kwargs': kwargs,
                    'task': TAKE_SKIP_TRAILING_STOP_V2_TARGET,
                    'feature_profile': feature_profile,
                    'seq_len': seq_len,
                    'best_metrics': best_metrics,
                },
                checkpoint_path,
            )
        else:
            stale_epochs += 1
            if stale_epochs >= patience:
                break

    if checkpoint_path.exists():
        ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
        model.load_state_dict(ckpt['model_state_dict'])

    validation_pred = _predict(model, validation_loader, device)
    test_pred = _predict(model, test_loader, device)
    validation_csv = run_dir / 'take_skip_trailing_stop_v2_validation_predictions.csv'
    test_csv = run_dir / 'take_skip_trailing_stop_v2_test_predictions.csv'
    _export_predictions(validation_csv, validation_arrays, validation_pred, target_columns)
    _export_predictions(test_csv, test_arrays, test_pred, target_columns)

    benchmark_dir = run_dir / 'benchmark'
    benchmark = run_benchmark(
        validation_csv=validation_csv,
        test_csv=test_csv,
        output_dir=benchmark_dir,
        min_pf=min_pf,
        min_trades_per_year=min_trades_per_year,
        targets=target_columns,
    )

    summary = {
        'config': {
            'feature_profile': feature_profile,
            'seq_len': seq_len,
            'epochs': epochs,
            'patience': patience,
            'batch_size': batch_size,
            'seed': seed,
            'target_columns': list(target_columns),
            'model_kwargs': kwargs,
        },
        'train_result': {
            'best_epoch': best_epoch,
            'best_score': best_score,
            'best_metrics': best_metrics,
            'history': history,
        },
        'checkpoint_path': str(checkpoint_path),
        'exports': {
            'validation_csv': str(validation_csv),
            'test_csv': str(test_csv),
        },
        'benchmark': benchmark,
        'runtime_sec': time.time() - started_at,
    }
    (run_dir / 'summary.json').write_text(json.dumps(_json_safe(summary), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[done] {run_dir.name}: runtime_sec={summary["runtime_sec"]:.1f}', flush=True)
    return summary


def _run_single_config_from_files(
    *,
    output_root: Path,
    feature_profile: str,
    seq_len: int,
    epochs: int,
    patience: int,
    batch_size: int,
    seed: int,
    min_pf: float,
    min_trades_per_year: float,
    target_columns: tuple[str, ...] | None,
    torch_threads: int | None,
) -> dict[str, object]:
    if torch_threads is not None and torch_threads > 0:
        torch.set_num_threads(int(torch_threads))
    run_dir = output_root / config_slug(feature_profile, seq_len)
    log_dir = run_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / 'run.log'
    with log_path.open('w', encoding='utf-8') as log_file:
        with contextlib.redirect_stdout(log_file), contextlib.redirect_stderr(log_file):
            print(f'[worker-start] {run_dir.name}', flush=True)
            train_frame = _read_labeled_csv(TRAIN_FILE)
            validation_frame = _read_labeled_csv(VAL_FILE)
            test_frame = _read_labeled_csv(TEST_FILE)
            result = run_single_config_from_frames(
                train_frame=train_frame,
                validation_frame=validation_frame,
                test_frame=test_frame,
                output_root=output_root,
                feature_profile=feature_profile,
                seq_len=seq_len,
                epochs=epochs,
                patience=patience,
                batch_size=batch_size,
                seed=seed,
                min_pf=min_pf,
                min_trades_per_year=min_trades_per_year,
                target_columns=target_columns,
                torch_threads=torch_threads,
            )
            print(f'[worker-done] {run_dir.name}', flush=True)
            return result


def run_matrix(
    *,
    output_dir: Path,
    feature_profiles: tuple[str, ...],
    seq_lens: tuple[int, ...],
    epochs: int,
    patience: int,
    batch_size: int,
    seed: int,
    min_pf: float,
    min_trades_per_year: float,
    target_columns: tuple[str, ...] | None = None,
    jobs: int | str = AUTO_VALUE,
    torch_threads: int | str | None = AUTO_VALUE,
    cpu_load: float = 0.5,
) -> dict[str, object]:
    started_at = time.time()
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f'[matrix-load] train={TRAIN_FILE}', flush=True)
    train_frame = _read_labeled_csv(TRAIN_FILE)
    resolved_target_columns = resolve_target_columns(train_frame, target_columns)
    configs = [
        (feature_profile, seq_len)
        for feature_profile in feature_profiles
        for seq_len in seq_lens
    ]
    cpu_schedule = resolve_cpu_schedule(
        config_count=len(configs),
        jobs=jobs,
        torch_threads=torch_threads,
        cpu_load=cpu_load,
    )
    resolved_jobs = int(cpu_schedule['jobs'])
    resolved_torch_threads = int(cpu_schedule['torch_threads'])
    print(
        f'[cpu-auto] cpu_count={cpu_schedule["cpu_count"]} cpu_load={cpu_schedule["cpu_load"]:.2f} target_threads={cpu_schedule["target_threads"]} jobs={resolved_jobs} torch_threads={resolved_torch_threads}',
        flush=True,
    )
    print(
        f'[matrix-start] configs={len(configs)} jobs={resolved_jobs} torch_threads={resolved_torch_threads} targets={len(resolved_target_columns)}',
        flush=True,
    )
    runs = []
    if resolved_jobs <= 1:
        print(f'[matrix-load] validation={VAL_FILE}', flush=True)
        validation_frame = _read_labeled_csv(VAL_FILE)
        print(f'[matrix-load] test={TEST_FILE}', flush=True)
        test_frame = _read_labeled_csv(TEST_FILE)
        for feature_profile, seq_len in configs:
            print(f'[matrix-run] {config_slug(feature_profile, seq_len)}', flush=True)
            runs.append(
                run_single_config_from_frames(
                    train_frame=train_frame,
                    validation_frame=validation_frame,
                    test_frame=test_frame,
                    output_root=output_dir,
                    feature_profile=feature_profile,
                    seq_len=seq_len,
                    epochs=epochs,
                    patience=patience,
                    batch_size=batch_size,
                    seed=seed,
                    min_pf=min_pf,
                    min_trades_per_year=min_trades_per_year,
                    target_columns=resolved_target_columns,
                    torch_threads=resolved_torch_threads,
                )
            )
    else:
        with ProcessPoolExecutor(max_workers=resolved_jobs) as executor:
            futures = {
                executor.submit(
                    _run_single_config_from_files,
                    output_root=output_dir,
                    feature_profile=feature_profile,
                    seq_len=seq_len,
                    epochs=epochs,
                    patience=patience,
                    batch_size=batch_size,
                    seed=seed,
                    min_pf=min_pf,
                    min_trades_per_year=min_trades_per_year,
                    target_columns=resolved_target_columns,
                    torch_threads=resolved_torch_threads,
                ): config_slug(feature_profile, seq_len)
                for feature_profile, seq_len in configs
            }
            for future in as_completed(futures):
                slug = futures[future]
                result = future.result()
                print(f'[matrix-complete] {slug}', flush=True)
                runs.append(result)
    manifest = {
        'runs': runs,
        'feature_profiles': list(feature_profiles),
        'seq_lens': list(seq_lens),
        'target_columns': list(resolved_target_columns),
        'jobs': resolved_jobs,
        'torch_threads': resolved_torch_threads,
        'cpu_schedule': cpu_schedule,
        'runtime_sec': time.time() - started_at,
    }
    (output_dir / 'manifest.json').write_text(json.dumps(_json_safe(manifest), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[matrix-done] runtime_sec={manifest["runtime_sec"]:.1f}', flush=True)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run take_skip_v2 lib_PIC feature training matrix.')
    parser.add_argument('--output-dir', type=Path, default=Path('ML/reports/take_skip_lib_pic_feature_matrix'))
    parser.add_argument('--feature-profiles', nargs='+', default=list(DEFAULT_FEATURE_PROFILES))
    parser.add_argument('--seq-lens', nargs='+', type=int, default=list(DEFAULT_SEQ_LENS))
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--patience', type=int, default=4)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--min-pf', type=float, default=1.0)
    parser.add_argument('--min-trades-per-year', type=float, default=6.0)
    parser.add_argument('--target-columns', nargs='+', default=None)
    parser.add_argument('--jobs', default=AUTO_VALUE)
    parser.add_argument('--torch-threads', default=AUTO_VALUE)
    parser.add_argument('--cpu-load', type=float, default=0.5)
    return parser.parse_args()


def main() -> dict[str, object]:
    args = parse_args()
    manifest = run_matrix(
        output_dir=args.output_dir,
        feature_profiles=tuple(args.feature_profiles),
        seq_lens=tuple(args.seq_lens),
        epochs=args.epochs,
        patience=args.patience,
        batch_size=args.batch_size,
        seed=args.seed,
        min_pf=args.min_pf,
        min_trades_per_year=args.min_trades_per_year,
        target_columns=tuple(args.target_columns) if args.target_columns else None,
        jobs=args.jobs,
        torch_threads=args.torch_threads,
        cpu_load=args.cpu_load,
    )
    print(json.dumps(_json_safe(manifest), ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    main()
