# =============================================================================
# Файл: run_take_skip_original_contour_feature_matrix.py
# Назначение: Training matrix для take_skip_v2 в старом single-tensor контуре.
# Обновлён: 2026-04-20
# Входные данные:
#   - DATA/Nero_train_labeled.csv
#   - DATA/Nero_validation_labeled.csv
#   - DATA/Nero_test_labeled.csv
# Выходные данные:
#   - ML/reports/take_skip_original_contour_feature_matrix/
# Использование:
#   python -m ML.run_take_skip_original_contour_feature_matrix --feature-modes original_baseline --seq-lens 50
# Примечания:
#   - Это research runner; общий ML.train не меняется.
#   - В отличие от dual-stream runner, все признаки добавляются в один 3D tensor.
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
from ML.data_loader import parse_fractals_to_3d
from ML.data_loader import TEST_FILE, TRAIN_FILE, VAL_FILE
from ML.lib_pic_feature_profiles import build_lib_pic_feature_parts
from ML.models.transformer import TransformerClassifier
from ML.multi_scale_fractal_features import build_multi_scale_fractal_features
from ML.take_skip_trailing_stop_v2_task import (
    TAKE_SKIP_THRESHOLD_ATR_V2,
    TAKE_SKIP_TRAILING_STOP_V2_COLUMNS,
    TAKE_SKIP_TRAILING_STOP_V2_TARGET,
)
from ML.utils import get_device, set_seed


ORIGINAL_BASELINE_ROW_FEATURE_COLUMNS = (
    'predict',
    'ATR',
    'session_hour',
    'weekday',
    'range_atr_6',
    'body_atr_3',
    'ret_dir_atr_lag1',
    'vol_regime_24',
    'ret_6_dir_atr',
    'ret_12_dir_atr',
    'ret_24_dir_atr',
    'fav_3_atr',
    'adv_3_atr',
    'fav_6_atr',
    'adv_6_atr',
    'fav_12_atr',
    'adv_12_atr',
    'fav_24_atr',
    'adv_24_atr',
)
LIVE_SAFE_BASELINE_ROW_FEATURE_COLUMNS = (
    'ATR',
    'session_hour',
    'weekday',
    'range_atr_6',
    'body_atr_3',
    'vol_regime_24',
)
FEATURE_MODES = (
    'original_baseline',
    'original_plus_path',
    'original_plus_geometry_path',
    'live_safe_baseline',
)
DEFAULT_SEQ_LENS = (20, 50, 100)
AUTO_VALUE = 'auto'


@dataclass(frozen=True)
class OriginalContourArrays:
    """Массивы старого take/skip контура.

    Атрибуты:
        X: Один 3D tensor shape (N, seq_len, feature_dim).
        mask: Маска валидных фракталов shape (N, seq_len).
        y: Бинарные take/skip цели shape (N, target_count).
        signal: Направление сигнала shape (N,).
        times: Время строк shape (N,).
        true_pnl: Реальный trailing-stop PnL shape (N, target_count).
        target_columns: Имена take/skip целей.
        parsed_X: Исходный parsed tensor shape (N, 100, 20), до добавления каналов.
        engineered: Повторяемые engineered-признаки shape (N, engineered_dim).
    """

    X: np.ndarray
    mask: np.ndarray
    y: np.ndarray
    signal: np.ndarray
    times: np.ndarray
    true_pnl: np.ndarray
    target_columns: tuple[str, ...]
    parsed_X: np.ndarray
    engineered: np.ndarray


class OriginalContourDataset(Dataset):
    """Dataset для старого single-tensor take/skip контура."""

    def __init__(self, arrays: OriginalContourArrays):
        self.X = torch.from_numpy(arrays.X.astype(np.float32)).float()
        self.mask = torch.from_numpy(arrays.mask.astype(bool)).bool()
        self.y = torch.from_numpy(arrays.y.astype(np.float32)).float()

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int):
        return self.X[idx], self.y[idx], self.mask[idx]


def target_to_true_pnl_column(target_column: str) -> str:
    _, horizon, x_suffix = target_column.split('_')
    return f'trail_{horizon}_pnl_atr_{x_suffix}'


def available_take_skip_v2_columns(
    frame: pd.DataFrame,
    requested: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    """Возвращает take/skip цели, для которых в DataFrame есть source PnL колонки."""
    candidates = tuple(requested) if requested is not None else tuple(TAKE_SKIP_TRAILING_STOP_V2_COLUMNS)
    missing_requested = [
        target
        for target in candidates
        if requested is not None and target_to_true_pnl_column(target) not in frame.columns
    ]
    if missing_requested:
        raise ValueError(f'missing requested take/skip v2 source columns: {missing_requested}')
    available = tuple(target for target in candidates if target_to_true_pnl_column(target) in frame.columns)
    if not available:
        raise ValueError('no take/skip v2 source columns found')
    return available


def build_original_baseline_features(frame: pd.DataFrame, parsed_X: np.ndarray) -> np.ndarray:
    """Строит baseline-признаки старого take/skip контура."""
    summary = build_multi_scale_fractal_features(parsed_X)
    row_features = (
        frame.reindex(columns=ORIGINAL_BASELINE_ROW_FEATURE_COLUMNS)
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0.0)
        .to_numpy(dtype=np.float32)
    )
    engineered = np.concatenate([summary, row_features], axis=1)
    return np.nan_to_num(engineered, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32, copy=False)


def build_live_safe_baseline_features(frame: pd.DataFrame, parsed_X: np.ndarray) -> np.ndarray:
    """Строит take/skip baseline без future-derived row-признаков."""
    summary = build_multi_scale_fractal_features(parsed_X)
    row_features = (
        frame.reindex(columns=LIVE_SAFE_BASELINE_ROW_FEATURE_COLUMNS)
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0.0)
        .to_numpy(dtype=np.float32)
    )
    engineered = np.concatenate([summary, row_features], axis=1)
    return np.nan_to_num(engineered, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32, copy=False)


def build_original_contour_engineered_features(
    frame: pd.DataFrame,
    parsed_X: np.ndarray,
    *,
    feature_mode: str,
    seq_len: int,
) -> np.ndarray:
    """Строит engineered-блок старого baseline плюс выбранные новые lib_PIC признаки."""
    if feature_mode not in FEATURE_MODES:
        available = ', '.join(FEATURE_MODES)
        raise ValueError(f'unknown feature_mode: {feature_mode}. Available: {available}')

    if feature_mode == 'live_safe_baseline':
        return build_live_safe_baseline_features(frame, parsed_X)

    blocks = [build_original_baseline_features(frame, parsed_X)]
    if feature_mode != 'original_baseline':
        parts = build_lib_pic_feature_parts(frame, seq_len=seq_len)
        blocks.append(parts['path'].to_numpy(dtype=np.float32))
        if feature_mode == 'original_plus_geometry_path':
            blocks.append(parts['geometry'].to_numpy(dtype=np.float32))
    engineered = np.concatenate(blocks, axis=1)
    return np.nan_to_num(engineered, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32, copy=False)


def append_repeated_channels(X: np.ndarray, engineered: np.ndarray) -> np.ndarray:
    """Повторяет строковые engineered-признаки на каждом шаге sequence tensor."""
    if len(X) != len(engineered):
        raise ValueError('X and engineered must have the same row count')
    repeated = np.repeat(np.asarray(engineered, dtype=np.float32)[:, None, :], X.shape[1], axis=1)
    return np.concatenate([X.astype(np.float32, copy=False), repeated], axis=2).astype(np.float32, copy=False)


def _split_targets(frame: pd.DataFrame, target_columns: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    source_columns = [target_to_true_pnl_column(target) for target in target_columns]
    missing = [column for column in source_columns if column not in frame.columns]
    if missing:
        raise ValueError(f'missing take/skip v2 source columns: {missing}')
    true_pnl = frame[source_columns].to_numpy(dtype=np.float32)
    y = (true_pnl >= TAKE_SKIP_THRESHOLD_ATR_V2).astype(np.float32)
    return y, true_pnl


def build_original_contour_arrays(
    frame: pd.DataFrame,
    *,
    feature_mode: str,
    seq_len: int,
    target_columns: tuple[str, ...] | None = None,
) -> OriginalContourArrays:
    """Собирает один single-tensor dataset для старого take/skip контура."""
    resolved_targets = available_take_skip_v2_columns(frame, target_columns)
    parsed_X, mask = parse_fractals_to_3d(frame)
    seq_len = int(seq_len)
    if not 1 <= seq_len <= parsed_X.shape[1]:
        raise ValueError(f'seq_len must be in [1, {parsed_X.shape[1]}], got {seq_len}')

    engineered = build_original_contour_engineered_features(frame, parsed_X, feature_mode=feature_mode, seq_len=seq_len)
    X = append_repeated_channels(parsed_X, engineered)
    X = X[:, :seq_len, :]
    mask = mask[:, :seq_len]
    y, true_pnl = _split_targets(frame, resolved_targets)
    signal = pd.to_numeric(frame['signal'], errors='coerce').fillna(0).to_numpy(dtype=np.int64)
    times = frame['time'].astype(str).to_numpy(dtype=object)
    return OriginalContourArrays(
        X=X,
        mask=mask.astype(bool),
        y=y,
        signal=signal,
        times=times,
        true_pnl=true_pnl,
        target_columns=resolved_targets,
        parsed_X=parsed_X,
        engineered=engineered,
    )


def config_slug(feature_mode: str, seq_len: int) -> str:
    return f'{feature_mode}_seq{seq_len}'


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


def _read_labeled_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=';', low_memory=False)


def _make_loader(arrays: OriginalContourArrays, *, batch_size: int, shuffle: bool) -> DataLoader:
    return DataLoader(OriginalContourDataset(arrays), batch_size=batch_size, shuffle=shuffle, drop_last=False)


def _compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, target_columns: tuple[str, ...]) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=np.float32)
    y_prob = np.asarray(y_prob, dtype=np.float32)
    if y_true.shape != y_prob.shape:
        raise ValueError(f'y_true shape {y_true.shape} does not match y_prob shape {y_prob.shape}')
    if y_true.ndim != 2 or y_true.shape[1] != len(target_columns):
        raise ValueError(f'y_true must have shape (n, {len(target_columns)})')

    clipped = np.clip(y_prob, 1e-7, 1.0 - 1e-7)
    bce = -(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped))
    metrics: dict[str, float] = {'bce': float(np.mean(bce))}
    for idx, target in enumerate(target_columns):
        yt = y_true[:, idx]
        yp = y_prob[:, idx]
        metrics[f'positive_rate_{target}'] = float(np.mean(yt))
        metrics[f'brier_{target}'] = float(np.mean((yp - yt) ** 2))
    metrics['val_score'] = -metrics['bce']
    return metrics


def _train_one_epoch(model: nn.Module, loader: DataLoader, loss_fn: nn.Module, optimizer, device: torch.device) -> float:
    model.train()
    losses = []
    for X_batch, y_batch, mask_batch in loader:
        optimizer.zero_grad(set_to_none=True)
        logits = model(X_batch.to(device), mask=mask_batch.to(device))
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
        for X_batch, y_batch, mask_batch in loader:
            logits = model(X_batch.to(device), mask=mask_batch.to(device))
            loss = loss_fn(logits, y_batch.to(device))
            losses.append(float(loss.detach().cpu().item()))
            y_true.append(y_batch.cpu().numpy())
            y_prob.append(torch.sigmoid(logits).cpu().numpy())
    metrics = _compute_metrics(np.vstack(y_true), np.vstack(y_prob), target_columns)
    return float(np.mean(losses)) if losses else 0.0, metrics


def _predict(model: nn.Module, loader: DataLoader, device: torch.device) -> np.ndarray:
    model.eval()
    chunks = []
    with torch.no_grad():
        for X_batch, _y_batch, mask_batch in loader:
            logits = model(X_batch.to(device), mask=mask_batch.to(device))
            chunks.append(torch.sigmoid(logits).cpu().numpy())
    return np.vstack(chunks).astype(np.float32)


def _export_predictions(
    path: Path,
    arrays: OriginalContourArrays,
    pred_prob: np.ndarray,
) -> None:
    pred_prob = np.asarray(pred_prob, dtype=np.float32)
    if pred_prob.shape != arrays.y.shape:
        raise ValueError(f'pred_prob shape {pred_prob.shape} does not match target shape {arrays.y.shape}')
    frame = pd.DataFrame({'time': arrays.times, 'signal': arrays.signal})
    for idx, target in enumerate(arrays.target_columns):
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
    feature_mode: str,
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
    run_dir = output_root / config_slug(feature_mode, seq_len)
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f'[start] {run_dir.name}: feature_mode={feature_mode} seq_len={seq_len}', flush=True)

    resolved_targets = available_take_skip_v2_columns(train_frame, target_columns)
    for split_name, frame in [('validation', validation_frame), ('test', test_frame)]:
        split_targets = available_take_skip_v2_columns(frame, resolved_targets)
        if split_targets != resolved_targets:
            raise ValueError(f'{split_name} target columns differ from train target columns')

    train_arrays = build_original_contour_arrays(
        train_frame,
        feature_mode=feature_mode,
        seq_len=seq_len,
        target_columns=resolved_targets,
    )
    validation_arrays = build_original_contour_arrays(
        validation_frame,
        feature_mode=feature_mode,
        seq_len=seq_len,
        target_columns=resolved_targets,
    )
    test_arrays = build_original_contour_arrays(
        test_frame,
        feature_mode=feature_mode,
        seq_len=seq_len,
        target_columns=resolved_targets,
    )

    train_loader = _make_loader(train_arrays, batch_size=batch_size, shuffle=True)
    validation_loader = _make_loader(validation_arrays, batch_size=batch_size, shuffle=False)
    test_loader = _make_loader(test_arrays, batch_size=batch_size, shuffle=False)

    kwargs = dict(model_kwargs or {})
    kwargs.setdefault('input_features', int(train_arrays.X.shape[2]))
    kwargs.setdefault('num_classes', len(resolved_targets))
    device = get_device()
    model = TransformerClassifier(**kwargs).to(device)
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
        val_loss, metrics = _validate(model, validation_loader, loss_fn, device, resolved_targets)
        history.append({'epoch': epoch, 'train_loss': train_loss, 'val_loss': val_loss, **metrics})
        print(
            f'[epoch] {run_dir.name}: {epoch}/{epochs} train_loss={train_loss:.6f} val_loss={val_loss:.6f} bce={metrics["bce"]:.6f}',
            flush=True,
        )
        score = float(metrics['val_score'])
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
                    'feature_mode': feature_mode,
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
    _export_predictions(validation_csv, validation_arrays, validation_pred)
    _export_predictions(test_csv, test_arrays, test_pred)

    benchmark = run_benchmark(
        validation_csv=validation_csv,
        test_csv=test_csv,
        output_dir=run_dir / 'benchmark',
        min_pf=min_pf,
        min_trades_per_year=min_trades_per_year,
        targets=resolved_targets,
    )

    summary = {
        'config': {
            'feature_mode': feature_mode,
            'seq_len': seq_len,
            'epochs': epochs,
            'patience': patience,
            'batch_size': batch_size,
            'seed': seed,
            'target_columns': list(resolved_targets),
            'input_features': int(train_arrays.X.shape[2]),
            'engineered_features': int(train_arrays.engineered.shape[1]),
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
    feature_mode: str,
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
    run_dir = output_root / config_slug(feature_mode, seq_len)
    log_dir = run_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / 'run.log'
    with log_path.open('w', encoding='utf-8') as log_file:
        with contextlib.redirect_stdout(log_file), contextlib.redirect_stderr(log_file):
            print(f'[worker-start] {run_dir.name}', flush=True)
            result = run_single_config_from_frames(
                train_frame=_read_labeled_csv(TRAIN_FILE),
                validation_frame=_read_labeled_csv(VAL_FILE),
                test_frame=_read_labeled_csv(TEST_FILE),
                output_root=output_root,
                feature_mode=feature_mode,
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
    feature_modes: tuple[str, ...],
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
    clear_cache: bool = False,
) -> dict[str, object]:
    started_at = time.time()
    output_dir.mkdir(parents=True, exist_ok=True)
    if clear_cache:
        print('[cache] clear-cache requested; this runner reads CSV directly and has no npy cache', flush=True)
    print(f'[matrix-load] train={TRAIN_FILE}', flush=True)
    train_frame = _read_labeled_csv(TRAIN_FILE)
    resolved_targets = available_take_skip_v2_columns(train_frame, target_columns)
    configs = [(feature_mode, seq_len) for feature_mode in feature_modes for seq_len in seq_lens]
    cpu_schedule = resolve_cpu_schedule(
        config_count=len(configs),
        jobs=jobs,
        torch_threads=torch_threads,
        cpu_load=cpu_load,
    )
    resolved_jobs = int(cpu_schedule['jobs'])
    resolved_torch_threads = int(cpu_schedule['torch_threads'])
    print(
        f'[matrix-start] configs={len(configs)} jobs={resolved_jobs} torch_threads={resolved_torch_threads} targets={len(resolved_targets)}',
        flush=True,
    )

    runs = []
    if resolved_jobs <= 1:
        print(f'[matrix-load] validation={VAL_FILE}', flush=True)
        validation_frame = _read_labeled_csv(VAL_FILE)
        print(f'[matrix-load] test={TEST_FILE}', flush=True)
        test_frame = _read_labeled_csv(TEST_FILE)
        for feature_mode, seq_len in configs:
            slug = config_slug(feature_mode, seq_len)
            print(f'[matrix-run] {slug}', flush=True)
            runs.append(
                run_single_config_from_frames(
                    train_frame=train_frame,
                    validation_frame=validation_frame,
                    test_frame=test_frame,
                    output_root=output_dir,
                    feature_mode=feature_mode,
                    seq_len=seq_len,
                    epochs=epochs,
                    patience=patience,
                    batch_size=batch_size,
                    seed=seed,
                    min_pf=min_pf,
                    min_trades_per_year=min_trades_per_year,
                    target_columns=resolved_targets,
                    torch_threads=resolved_torch_threads,
                )
            )
            print(f'[matrix-complete] {slug}', flush=True)
    else:
        with ProcessPoolExecutor(max_workers=resolved_jobs) as executor:
            futures = {
                executor.submit(
                    _run_single_config_from_files,
                    output_root=output_dir,
                    feature_mode=feature_mode,
                    seq_len=seq_len,
                    epochs=epochs,
                    patience=patience,
                    batch_size=batch_size,
                    seed=seed,
                    min_pf=min_pf,
                    min_trades_per_year=min_trades_per_year,
                    target_columns=resolved_targets,
                    torch_threads=resolved_torch_threads,
                ): config_slug(feature_mode, seq_len)
                for feature_mode, seq_len in configs
            }
            for future in as_completed(futures):
                slug = futures[future]
                try:
                    result = future.result()
                except Exception:
                    print(f'[matrix-failed] {slug}', flush=True)
                    raise
                print(f'[matrix-complete] {slug}', flush=True)
                runs.append(result)

    manifest = {
        'runs': runs,
        'feature_modes': list(feature_modes),
        'seq_lens': list(seq_lens),
        'target_columns': list(resolved_targets),
        'jobs': resolved_jobs,
        'torch_threads': resolved_torch_threads,
        'cpu_schedule': cpu_schedule,
        'runtime_sec': time.time() - started_at,
    }
    (output_dir / 'manifest.json').write_text(json.dumps(_json_safe(manifest), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[matrix-done] runtime_sec={manifest["runtime_sec"]:.1f}', flush=True)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run take_skip_v2 original-contour feature matrix.')
    parser.add_argument('--output-dir', type=Path, default=Path('ML/reports/take_skip_original_contour_feature_matrix'))
    parser.add_argument('--feature-modes', nargs='+', default=list(FEATURE_MODES))
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
    parser.add_argument('--clear-cache', action='store_true')
    return parser.parse_args()


def main() -> dict[str, object]:
    args = parse_args()
    manifest = run_matrix(
        output_dir=args.output_dir,
        feature_modes=tuple(args.feature_modes),
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
        clear_cache=args.clear_cache,
    )
    print(json.dumps(_json_safe(manifest), ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    main()
