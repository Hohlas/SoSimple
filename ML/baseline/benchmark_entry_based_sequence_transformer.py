# =============================================================================
# Файл: benchmark_entry_based_sequence_transformer.py
# Назначение: DIAGNOSTIC_ONLY runner для проверки ordered fractal sequence
#   представления в entry-based next open постановке.
# Язык: Python 3.10+
# Обновлён: 2026-07-06
# =============================================================================

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor

from ML.baseline import benchmark_entry_based_next_open_closeout as closeout
from ML.baseline import benchmark_entry_based_powerful_tabular as powerful
from ML.models.transformer import PositionalEncoding


SEQUENCE_TRANSFORMER_SCHEMA_VERSION = 1
SEQUENCE_TRANSFORMER_OUTPUT_PREFIX = "entry_based_sequence_transformer"
REPORT_JSON_PATH = Path(f"ML/reports/{SEQUENCE_TRANSFORMER_OUTPUT_PREFIX}.json")
REPORT_METRICS_PATH = Path(f"ML/reports/{SEQUENCE_TRANSFORMER_OUTPUT_PREFIX}_metrics.csv")
REPORT_ROWS_PATH = Path(f"ML/reports/{SEQUENCE_TRANSFORMER_OUTPUT_PREFIX}_rows.csv")
REPORT_TENSOR_AUDIT_PATH = Path(f"ML/reports/{SEQUENCE_TRANSFORMER_OUTPUT_PREFIX}_tensor_audit.csv")
REPORT_LOG_PATH = Path(f"ML/reports/{SEQUENCE_TRANSFORMER_OUTPUT_PREFIX}_run.log")

SEQUENCE_TRANSFORMER_REPRESENTATIONS = (
    "all100_sequence",
    "nearest_k80_sequence",
    "nearest_k60_sequence",
)
SEQUENCE_TRANSFORMER_MODEL_KEYS = (
    "transformer_small",
    "transformer_medium",
    "sequence_flat_hist_gradient_boosting",
)
SEQUENCE_TRANSFORMER_SEEDS = (42,)
TARGET_HORIZONS = (3, 6, 12, 24)
PREDICTED_TARGET_FAMILIES = ("entry_log_ratio", "entry_up", "entry_dn")
TARGET_COLUMNS = tuple(f"{family}_{h}" for h in TARGET_HORIZONS for family in ("entry_up", "entry_dn", "entry_log_ratio"))

TOKEN_FEATURE_NAMES = (
    "direction",
    "front",
    "back",
    "strong",
    "break",
    "reverse",
    "power",
    "count",
    "impulse",
    "up_3",
    "dn_3",
    "up_6",
    "dn_6",
    "up_12",
    "dn_12",
    "up_24",
    "dn_24",
    "up_48",
    "dn_48",
    "log_fractal_atr_ratio",
    "log_shift",
    "log_delta_shift",
    "price_coord_atr",
    "abs_price_coord_atr",
    "dir_price_coord_atr",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
)

FORBIDDEN_INPUT_COLUMN_PATTERNS = (
    "up_",
    "dn_",
    "entry_up_",
    "entry_dn_",
    "entry_log_ratio_",
    "ret_",
    "fav_",
    "adv_",
    "target_",
    "label_",
    "outcome_",
    "predict",
    "signal",
)

SELECTION_POLICY = {
    "winner_metric": "val_select",
    "val_eval": "check_only",
    "low_n_disclosure_2026": "disclosure_only",
    "locked_test": "not_opened",
}
TRAINING_POLICY = {
    "mode": "fixed_epochs",
    "epochs": 60,
    "early_stopping": "disabled",
    "validation_used_for_early_stopping": False,
}

POWERFUL_SELECTED_BASELINE = {
    "representation": "nearest_k80",
    "model_key": "hist_gradient_boosting_strong",
    "horizon": "H12",
    "val_select": 0.0519,
    "val_eval": -0.0009,
}
POWERFUL_BEST_BY_EVAL_DISCLOSURE = {
    "representation": "corridor_5atr",
    "model_key": "extra_trees_regressor",
    "horizon": "H12",
    "val_select": 0.0042,
    "val_eval": 0.0475,
    "selection_forbidden": True,
}
CLOSEOUT_CANDIDATE_BASELINE = {
    "representation": "nearest_k60",
    "model_key": "xgboost_depth5",
    "horizon": "H12",
    "val_select": 0.0373,
    "val_eval": 0.0274,
}


@dataclass(frozen=True)
class SequenceTensor:
    tokens: np.ndarray
    mask: np.ndarray
    feature_names: tuple[str, ...]
    representation: str
    invalid_rows: tuple[int, ...] = ()


@dataclass(frozen=True)
class SequenceNormalizer:
    feature_names: tuple[str, ...]
    center: np.ndarray
    scale: np.ndarray
    fit_split: str
    n_fit_tokens: int


@dataclass(frozen=True)
class TargetNormalizer:
    target_order: tuple[str, ...]
    center: np.ndarray
    scale: np.ndarray
    fit_split: str


@dataclass(frozen=True)
class PreparedSequenceData:
    tensors: dict[str, SequenceTensor]
    targets: dict[str, np.ndarray]
    frames: dict[str, pd.DataFrame]
    target_normalizer: TargetNormalizer


def enumerate_sequence_transformer_jobs() -> list[dict[str, object]]:
    return [
        {"representation": representation, "model_key": model_key, "seed": seed}
        for representation, model_key, seed in product(
            SEQUENCE_TRANSFORMER_REPRESENTATIONS,
            SEQUENCE_TRANSFORMER_MODEL_KEYS,
            SEQUENCE_TRANSFORMER_SEEDS,
        )
    ]


def job_key(job: dict[str, object]) -> str:
    return f"{job['representation']}/{job['model_key']}/{job['seed']}"


def is_forbidden_input_column(column: str) -> bool:
    return any(column == pattern or column.startswith(pattern) for pattern in FORBIDDEN_INPUT_COLUMN_PATTERNS)


def _parse_fractal(raw: object) -> list[float] | None:
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return None
    text = str(raw).strip()
    if not text:
        return None
    parts = text.split(":")
    if len(parts) < 23:
        return None
    try:
        values = [float(part) for part in parts[:23]]
    except ValueError:
        return None
    if not np.isfinite(values).all():
        return None
    if values[21] <= 0:
        return None
    return values


def _calendar_features(value: object) -> tuple[float, float, float, float]:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        hour = 0.0
        dow = 0.0
    else:
        hour = float(timestamp.hour)
        dow = float(timestamp.dayofweek)
    return (
        math.sin(2.0 * math.pi * hour / 24.0),
        math.cos(2.0 * math.pi * hour / 24.0),
        math.sin(2.0 * math.pi * dow / 7.0),
        math.cos(2.0 * math.pi * dow / 7.0),
    )


def _token_from_values(values: list[float], token_index: int, row_atr: float, anchor_price: float, next_shift: float | None, calendar: tuple[float, float, float, float]) -> list[float]:
    price = values[1]
    direction = values[2]
    shift = values[22]
    delta_shift = 0.0 if next_shift is None else abs(shift - next_shift)
    price_coord = (price - anchor_price) / row_atr
    updn = (0.0,) * 10 if token_index == 0 else (
        values[17],
        values[18],
        values[19],
        values[20],
        values[11],
        values[12],
        values[13],
        values[14],
        values[15],
        values[16],
    )
    return [
        direction,
        values[3],
        values[4],
        values[5],
        values[6],
        values[7],
        values[8],
        values[9],
        values[10],
        *updn,
        math.log(max(values[21], 1e-12) / row_atr),
        math.log1p(max(shift, 0.0)),
        math.log1p(delta_shift),
        price_coord,
        abs(price_coord),
        price_coord * direction,
        *calendar,
    ]


def build_sequence_tensor(frame: pd.DataFrame, representation: str) -> SequenceTensor:
    if representation not in SEQUENCE_TRANSFORMER_REPRESENTATIONS:
        raise ValueError(f"unknown representation: {representation}")
    tokens = np.zeros((len(frame), 100, len(TOKEN_FEATURE_NAMES)), dtype=np.float32)
    mask = np.zeros((len(frame), 100), dtype=bool)
    keep_by_representation = {"all100_sequence": 100, "nearest_k80_sequence": 80, "nearest_k60_sequence": 60}
    keep_n = keep_by_representation[representation]

    for row_idx, (_, row) in enumerate(frame.iterrows()):
        row_atr = float(pd.to_numeric(row.get("ATR"), errors="coerce"))
        fractal0 = _parse_fractal(row.get("fractal0"))
        if not np.isfinite(row_atr) or row_atr <= 0.0 or fractal0 is None:
            raise ValueError(f"invalid ATR or fractal0 at row {row_idx}")
        parsed: list[tuple[int, list[float]]] = []
        for token_idx in range(100):
            values = _parse_fractal(row.get(f"fractal{token_idx}"))
            if values is not None:
                parsed.append((token_idx, values))
        if representation != "all100_sequence":
            parsed = sorted(parsed, key=lambda item: abs((item[1][1] - fractal0[1]) / row_atr))[:keep_n]
            parsed = sorted(parsed, key=lambda item: item[0])
        calendar = _calendar_features(row.get("time"))
        selected = parsed[:100]
        for out_idx, (token_idx, values) in enumerate(selected):
            next_shift = selected[out_idx + 1][1][22] if out_idx + 1 < len(selected) else None
            tokens[row_idx, out_idx, :] = np.asarray(
                _token_from_values(values, token_idx, row_atr, fractal0[1], next_shift, calendar),
                dtype=np.float32,
            )
            mask[row_idx, out_idx] = True
    return SequenceTensor(tokens=tokens, mask=mask, feature_names=TOKEN_FEATURE_NAMES, representation=representation)


def fit_sequence_normalizer(train: SequenceTensor) -> SequenceNormalizer:
    valid = train.tokens[train.mask]
    if valid.size == 0:
        raise ValueError("cannot fit normalizer without valid train tokens")
    center = np.nanmedian(valid, axis=0).astype(np.float32)
    q75 = np.nanpercentile(valid, 75, axis=0)
    q25 = np.nanpercentile(valid, 25, axis=0)
    scale = np.maximum(q75 - q25, 1e-6).astype(np.float32)
    return SequenceNormalizer(train.feature_names, center, scale, "train", int(valid.shape[0]))


def apply_sequence_normalizer(tensor: SequenceTensor, normalizer: SequenceNormalizer) -> SequenceTensor:
    if tuple(tensor.feature_names) != tuple(normalizer.feature_names):
        raise ValueError("feature_names mismatch")
    normalized = np.zeros_like(tensor.tokens, dtype=np.float32)
    normalized[tensor.mask] = np.clip((tensor.tokens[tensor.mask] - normalizer.center) / normalizer.scale, -10.0, 10.0)
    return SequenceTensor(normalized, tensor.mask.copy(), tensor.feature_names, tensor.representation, tensor.invalid_rows)


def fit_target_normalizer(train_targets: np.ndarray) -> TargetNormalizer:
    center = np.nanmedian(train_targets, axis=0).astype(np.float32)
    q75 = np.nanpercentile(train_targets, 75, axis=0)
    q25 = np.nanpercentile(train_targets, 25, axis=0)
    scale = np.maximum(q75 - q25, 1e-6).astype(np.float32)
    return TargetNormalizer(TARGET_COLUMNS, center, scale, "train")


def normalize_targets(targets: np.ndarray, normalizer: TargetNormalizer) -> np.ndarray:
    return np.clip((targets - normalizer.center) / normalizer.scale, -10.0, 10.0).astype(np.float32)


def inverse_normalize_targets(targets: np.ndarray, normalizer: TargetNormalizer) -> np.ndarray:
    return (targets * normalizer.scale + normalizer.center).astype(np.float32)


def audit_sequence_tensor(tensors: dict[str, SequenceTensor]) -> dict[str, object]:
    profiles: dict[str, object] = {}
    warnings: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for split_name, tensor in tensors.items():
        invalid_values = int((~np.isfinite(tensor.tokens)).sum())
        padding_nonzero = int(np.count_nonzero(tensor.tokens[~tensor.mask]))
        rows_without_tokens = int((~tensor.mask.any(axis=1)).sum())
        valid_values = tensor.tokens[tensor.mask]
        valid_token_rate = float(tensor.mask.mean()) if tensor.mask.size else 0.0
        tails: dict[str, dict[str, float]] = {}
        near_constant: list[str] = []
        if valid_values.size:
            for idx, name in enumerate(tensor.feature_names):
                values = valid_values[:, idx]
                tails[name] = {
                    "abs_gt_3": float(np.mean(np.abs(values) > 3.0)),
                    "abs_gt_5": float(np.mean(np.abs(values) > 5.0)),
                    "abs_gt_10": float(np.mean(np.abs(values) > 10.0)),
                }
                if np.nanstd(values) <= 1e-9:
                    near_constant.append(name)
                if tails[name]["abs_gt_10"] > 0.01:
                    warnings.append({"split": split_name, "feature": name, "family": "TAIL_GT10", "rate": tails[name]["abs_gt_10"]})
        if invalid_values:
            errors.append({"split": split_name, "family": "NAN_INF", "count": invalid_values})
        if padding_nonzero:
            errors.append({"split": split_name, "family": "PADDING_NOT_ZERO", "count": padding_nonzero})
        if rows_without_tokens:
            errors.append({"split": split_name, "family": "NO_VALID_TOKENS", "count": rows_without_tokens})
        profiles[split_name] = {
            "rows": int(tensor.tokens.shape[0]),
            "valid_token_rate": valid_token_rate,
            "padding_rate": 1.0 - valid_token_rate,
            "nan_inf_count": invalid_values,
            "padding_nonzero_count": padding_nonzero,
            "rows_without_valid_tokens": rows_without_tokens,
            "tail_rates": tails,
            "near_constant_fields": near_constant,
        }
    status = "ERROR" if errors else ("WARNING" if warnings else "PASS")
    decisions = {
        str(warning["family"]): {
            "decision": "accept_as_warning",
            "reason": "diagnostic stage; warning is disclosed",
        }
        for warning in warnings
    }
    return {"status": status, "profiles": profiles, "warnings": warnings, "errors": errors, "audit_decisions": decisions}


class SequenceTransformerRegressor(torch.nn.Module):
    def __init__(self, input_features: int, output_dim: int, d_model: int, nhead: int, num_layers: int, dropout: float):
        super().__init__()
        self.input_projection = torch.nn.Linear(input_features, d_model)
        self.cls_token = torch.nn.Parameter(torch.randn(1, 1, d_model) * 0.02)
        self.pos_encoding = PositionalEncoding(d_model, max_len=128, dropout=dropout)
        layer = torch.nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 2,
            dropout=dropout,
            activation="relu",
            batch_first=True,
        )
        self.encoder = torch.nn.TransformerEncoder(layer, num_layers=num_layers)
        self.head = torch.nn.Sequential(
            torch.nn.Dropout(dropout),
            torch.nn.Linear(d_model, d_model // 2),
            torch.nn.ReLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(d_model // 2, output_dim),
        )

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        batch_size = x.size(0)
        projected = self.input_projection(x)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        encoded = torch.cat([cls_tokens, projected], dim=1)
        encoded = self.pos_encoding(encoded)
        src_key_padding_mask = None
        if mask is not None:
            cls_mask = torch.ones(batch_size, 1, dtype=torch.bool, device=mask.device)
            src_key_padding_mask = ~torch.cat([cls_mask, mask], dim=1)
        encoded = self.encoder(encoded, src_key_padding_mask=src_key_padding_mask)
        return self.head(encoded[:, 0, :])


def _transformer_config(model_key: str) -> dict[str, object]:
    if model_key == "transformer_small":
        return {"d_model": 64, "nhead": 4, "num_layers": 2, "dropout": 0.20}
    if model_key == "transformer_medium":
        return {"d_model": 128, "nhead": 8, "num_layers": 3, "dropout": 0.20}
    raise ValueError(f"not a transformer model: {model_key}")


def train_sequence_model(
    job: dict[str, object],
    data: PreparedSequenceData,
    max_epochs: int = 60,
    batch_size: int = 512,
    device: str = "cpu",
    threads: int = 24,
    heartbeat_prefix: str | None = None,
) -> dict[str, object]:
    torch.set_num_threads(int(threads))
    started = time.time()
    seed = int(job["seed"])
    np.random.seed(seed)
    torch.manual_seed(seed)
    model_key = str(job["model_key"])
    train_tensor = data.tensors["train"]
    y_train_norm = normalize_targets(data.targets["train"], data.target_normalizer)
    predictions_by_split: dict[str, pd.DataFrame] = {}
    model_metadata: dict[str, object]

    if model_key == "sequence_flat_hist_gradient_boosting":
        x_train = np.concatenate(
            [train_tensor.tokens.reshape(len(train_tensor.tokens), -1), train_tensor.mask.astype(np.float32)],
            axis=1,
        )
        model = MultiOutputRegressor(HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, random_state=seed))
        model.fit(x_train, y_train_norm)
        for split_name, tensor in data.tensors.items():
            x_eval = np.concatenate([tensor.tokens.reshape(len(tensor.tokens), -1), tensor.mask.astype(np.float32)], axis=1)
            preds_norm = np.asarray(model.predict(x_eval), dtype=np.float32)
            predictions_by_split[split_name] = closeout.closeout_predictions_frame(inverse_normalize_targets(preds_norm, data.target_normalizer))
        model_metadata = {"model_key": model_key, "family": "hist_gradient_boosting", "seed": seed, "max_iter": 200}
    else:
        config = _transformer_config(model_key)
        resolved_device = torch.device(device)
        model = SequenceTransformerRegressor(len(train_tensor.feature_names), len(TARGET_COLUMNS), **config).to(resolved_device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
        loss_fn = torch.nn.MSELoss()
        x = torch.as_tensor(train_tensor.tokens, dtype=torch.float32)
        m = torch.as_tensor(train_tensor.mask, dtype=torch.bool)
        y = torch.as_tensor(y_train_norm, dtype=torch.float32)
        dataset = torch.utils.data.TensorDataset(x, m, y)
        generator = torch.Generator().manual_seed(seed)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True, generator=generator)
        losses: list[float] = []
        model.train()
        train_started = time.time()
        for epoch in range(1, max_epochs + 1):
            epoch_losses: list[float] = []
            for xb, mb, yb in loader:
                xb, mb, yb = xb.to(resolved_device), mb.to(resolved_device), yb.to(resolved_device)
                optimizer.zero_grad(set_to_none=True)
                loss = loss_fn(model(xb, mb), yb)
                loss.backward()
                optimizer.step()
                epoch_losses.append(float(loss.detach().cpu()))
            losses.append(float(np.mean(epoch_losses)) if epoch_losses else 0.0)
            if heartbeat_prefix and (epoch == 1 or epoch == max_epochs or epoch % 5 == 0):
                elapsed = time.time() - train_started
                eta = elapsed / epoch * (max_epochs - epoch) if epoch else 0.0
                print(
                    f"[heartbeat] {heartbeat_prefix}: epoch={epoch}/{max_epochs}, "
                    f"loss={losses[-1]:.6f}, elapsed={elapsed:.1f}s, eta={eta:.1f}s",
                    flush=True,
                )
        model.eval()
        with torch.no_grad():
            for split_name, tensor in data.tensors.items():
                preds: list[np.ndarray] = []
                for start in range(0, len(tensor.tokens), batch_size):
                    xb = torch.as_tensor(tensor.tokens[start : start + batch_size], dtype=torch.float32, device=resolved_device)
                    mb = torch.as_tensor(tensor.mask[start : start + batch_size], dtype=torch.bool, device=resolved_device)
                    preds.append(model(xb, mb).detach().cpu().numpy())
                preds_norm = np.concatenate(preds, axis=0) if preds else np.zeros((0, len(TARGET_COLUMNS)), dtype=np.float32)
                predictions_by_split[split_name] = closeout.closeout_predictions_frame(inverse_normalize_targets(preds_norm, data.target_normalizer))
        model_metadata = {"model_key": model_key, "family": "transformer", "seed": seed, **config, "epochs": max_epochs, "loss_last": losses[-1] if losses else None}

    return {
        "predictions_by_split": predictions_by_split,
        "model_metadata": model_metadata,
        "elapsed_sec": time.time() - started,
        "batch_size": batch_size,
        "device": device,
        "torch_thread_count": torch.get_num_threads(),
    }


def _metric_value(run: dict[str, object], split_name: str, target_family: str, horizon: int) -> float:
    payload = run.get("split_metrics", {}).get(split_name, {}).get(f"{target_family}_{horizon}", {})
    return float(payload.get("spearman") or 0.0)


def _trade_value(run: dict[str, object], split_name: str, horizon: int) -> float:
    payload = run.get("split_metrics", {}).get(split_name, {}).get(f"simple_trade_{horizon}", {})
    return float(payload.get("mean_signed_log_ratio", payload.get("mean", 0.0)) or 0.0)


def yearly_check_pass_for_run(run: dict[str, object], target_family: str, horizon: int) -> bool:
    metric_key = f"{target_family}_{horizon}"
    for split_name in ("val_select", "val_eval"):
        by_year = run.get("yearly_metrics", {}).get(split_name, {})
        scores = [
            float(payload.get(metric_key, {}).get("spearman", 0.0) or 0.0)
            for _, payload in sorted(by_year.items())
            if isinstance(payload, dict) and metric_key in payload
        ]
        positive_scores = [score for score in scores if score > 0.0]
        if len(scores) < 2 or len(positive_scores) < 2:
            return False
        total_positive = sum(positive_scores)
        best_year_share = max(positive_scores) / total_positive if total_positive > 0 else 1.0
        without_best_year_score = (sum(scores) - max(scores)) / (len(scores) - 1)
        if best_year_share >= 0.80 or without_best_year_score <= 0.0:
            return False
    return True


def compute_yearly_metrics(frame: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, object]:
    timestamps = pd.to_datetime(frame["time"], errors="coerce")
    result: dict[str, object] = {}
    for year in range(2021, 2026):
        year_mask = timestamps.dt.year == year
        if int(year_mask.sum()) == 0:
            result[str(year)] = {"rows": 0}
        else:
            result[str(year)] = {"rows": int(year_mask.sum()), **closeout.compute_closeout_split_metrics(frame.loc[year_mask].reset_index(drop=True), predictions.loc[year_mask].reset_index(drop=True))}
    return result


def score_sequence_predictions(runs: list[dict[str, object]]) -> list[dict[str, object]]:
    all100_lookup = {
        (run.get("model_key"), run.get("seed")): run
        for run in runs
        if run.get("representation") == "all100_sequence"
    }
    rows: list[dict[str, object]] = []
    for run in runs:
        all100 = all100_lookup.get((run.get("model_key"), run.get("seed")))
        for family in PREDICTED_TARGET_FAMILIES:
            for horizon in TARGET_HORIZONS:
                row = {
                    "representation": run["representation"],
                    "model_key": run["model_key"],
                    "seed": run["seed"],
                    "target_family": family,
                    "horizon": horizon,
                    "val_select": _metric_value(run, "val_select", family, horizon),
                    "val_eval": _metric_value(run, "val_eval", family, horizon),
                    "low_n_disclosure": _metric_value(run, "low_n_disclosure", family, horizon),
                    "simple_trade_val_select": _trade_value(run, "val_select", horizon),
                    "simple_trade_val_eval": _trade_value(run, "val_eval", horizon),
                    "powerful_selected_baseline": POWERFUL_SELECTED_BASELINE,
                    "powerful_best_by_val_eval_disclosure": POWERFUL_BEST_BY_EVAL_DISCLOSURE,
                    "closeout_candidate_baseline": CLOSEOUT_CANDIDATE_BASELINE,
                    "yearly_check_pass": yearly_check_pass_for_run(run, family, horizon),
                }
                if all100 is not None:
                    row["matching_all100_val_select"] = _metric_value(all100, "val_select", family, horizon)
                    row["matching_all100_val_eval"] = _metric_value(all100, "val_eval", family, horizon)
                rows.append(row)
    return rows


def select_winner_by_policy(rows: list[dict[str, object]], selection_policy: dict[str, object]) -> dict[str, object]:
    metric = str(selection_policy["winner_metric"])
    return max(rows, key=lambda row: float(row.get(metric, 0.0) or 0.0), default={})


def decide_sequence_verdict(rows: list[dict[str, object]], smoke_check: dict[str, object], tensor_audit: dict[str, object]) -> dict[str, object]:
    if smoke_check.get("status") != "PASS" or tensor_audit.get("status") == "ERROR":
        return {"verdict": "ABORT_CONTRACT_FAIL"}
    direction_rows = [row for row in rows if row.get("target_family") == "entry_log_ratio" and row.get("representation") != "all100_sequence"]
    best_direction = select_winner_by_policy(direction_rows, SELECTION_POLICY)
    amplitude_rows = [row for row in rows if row.get("target_family") in {"entry_up", "entry_dn"}]
    best_amplitude = select_winner_by_policy(amplitude_rows, SELECTION_POLICY)
    direction_pass = bool(best_direction) and (
        float(best_direction.get("val_select", 0.0) or 0.0) >= 0.10
        and float(best_direction.get("val_eval", 0.0) or 0.0) >= 0.05
        and float(best_direction.get("val_select", 0.0) or 0.0) > POWERFUL_SELECTED_BASELINE["val_select"]
        and float(best_direction.get("val_eval", 0.0) or 0.0) > POWERFUL_SELECTED_BASELINE["val_eval"]
        and float(best_direction.get("val_select", 0.0) or 0.0) > CLOSEOUT_CANDIDATE_BASELINE["val_select"]
        and float(best_direction.get("val_eval", 0.0) or 0.0) > CLOSEOUT_CANDIDATE_BASELINE["val_eval"]
        and not (
            float(best_direction.get("matching_all100_val_select", -999.0) or 0.0) > float(best_direction.get("val_select", 0.0) or 0.0)
            and float(best_direction.get("matching_all100_val_eval", -999.0) or 0.0) > float(best_direction.get("val_eval", 0.0) or 0.0)
        )
        and float(best_direction.get("simple_trade_val_select", 0.0) or 0.0) > 0.0
        and float(best_direction.get("simple_trade_val_eval", 0.0) or 0.0) > 0.0
        and bool(best_direction.get("yearly_check_pass", False))
    )
    if direction_pass:
        return {"verdict": "DIRECTION_REPLICATION_REQUIRED", "best_direction_candidate_only": best_direction}
    if best_amplitude and float(best_amplitude.get("val_select", 0.0) or 0.0) >= 0.25 and float(best_amplitude.get("val_eval", 0.0) or 0.0) >= 0.15:
        return {"verdict": "PIVOT_AMPLITUDE", "best_amplitude": best_amplitude, "best_direction_candidate_only": best_direction}
    return {"verdict": "REJECT_SEQUENCE_CAPACITY_EXPLANATION", "best_direction_candidate_only": best_direction, "best_amplitude": best_amplitude}


def run_sequence_smoke_check(splits: dict[str, pd.DataFrame]) -> dict[str, object]:
    required = [f"{family}_{h}" for h in TARGET_HORIZONS for family in ("entry_up", "entry_dn", "entry_log_ratio")]
    failures: list[dict[str, object]] = []
    checks: dict[str, object] = {"row_counts": {}, "time_ranges": {}}
    for split_name, frame in splits.items():
        checks["row_counts"][split_name] = int(len(frame))
        missing = [column for column in required if column not in frame.columns]
        if missing:
            failures.append({"split": split_name, "check": "missing_targets", "columns": missing})
        for column in [c for c in required if c in frame.columns]:
            values = pd.to_numeric(frame[column], errors="coerce")
            if not np.isfinite(values).all():
                failures.append({"split": split_name, "check": "nonfinite_target", "column": column})
            if values.nunique(dropna=True) <= 1:
                failures.append({"split": split_name, "check": "constant_target", "column": column})
        if "entry_time" in frame.columns:
            signal_time = pd.to_datetime(frame["time"], errors="coerce")
            entry_time = pd.to_datetime(frame["entry_time"], errors="coerce")
            bad = int(((entry_time <= signal_time) | entry_time.isna() | signal_time.isna()).sum())
            if bad:
                failures.append({"split": split_name, "check": "entry_time_after_signal_time", "bad_rows": bad})
        times = pd.to_datetime(frame.get("time"), errors="coerce")
        checks["time_ranges"][split_name] = {
            "min": None if times.dropna().empty else times.min().isoformat(),
            "max": None if times.dropna().empty else times.max().isoformat(),
        }
    return {"status": "FAIL" if failures else "PASS", "checks": checks, "failures": failures}


def split_horizon_overlap_check(splits: dict[str, pd.DataFrame], horizons: tuple[int, ...] = TARGET_HORIZONS) -> dict[str, object]:
    return powerful.compute_split_horizon_overlap_check(splits)


def _build_sequence_data(splits: dict[str, pd.DataFrame], representation: str) -> tuple[PreparedSequenceData, dict[str, object]]:
    raw_tensors = {split: build_sequence_tensor(frame, representation) for split, frame in splits.items() if split in {"train", "val_select", "val_eval", "low_n_disclosure"}}
    normalizer = fit_sequence_normalizer(raw_tensors["train"])
    tensors = {split: apply_sequence_normalizer(tensor, normalizer) for split, tensor in raw_tensors.items()}
    targets = {split: closeout.closeout_target_matrix(frame) for split, frame in splits.items() if split in tensors}
    target_normalizer = fit_target_normalizer(targets["train"])
    contract = {
        "fit_split": normalizer.fit_split,
        "feature_names": normalizer.feature_names,
        "center": normalizer.center,
        "scale": normalizer.scale,
        "n_fit_tokens": normalizer.n_fit_tokens,
        "padding_values": 0.0,
        "validation_splits_do_not_fit": ("val_select", "val_eval", "low_n_disclosure"),
    }
    return PreparedSequenceData(tensors, targets, {name: splits[name] for name in tensors}, target_normalizer), contract


def build_target_normalization_contract(train_frame: pd.DataFrame) -> dict[str, object]:
    normalizer = fit_target_normalizer(closeout.closeout_target_matrix(train_frame))
    return {
        "fit_split": "train",
        "target_order": normalizer.target_order,
        "scaler": "median_iqr",
        "center": normalizer.center,
        "scale": normalizer.scale,
        "scale_floor": 1e-6,
        "clip": [-10.0, 10.0],
        "input_and_target_scalers_separate": True,
        "inverse_transform_before_metrics": True,
    }


def evaluate_sequence_job(job: dict[str, object], splits: dict[str, pd.DataFrame], args: argparse.Namespace) -> dict[str, object]:
    started = time.time()
    data, normalization_contract = _build_sequence_data(splits, str(job["representation"]))
    fitted = train_sequence_model(
        job,
        data,
        max_epochs=args.max_epochs,
        batch_size=args.batch_size,
        device=args.resolved_device,
        threads=args.threads,
        heartbeat_prefix=f"train:{job_key(job)}",
    )
    split_metrics = {
        split_name: closeout.compute_closeout_split_metrics(splits[split_name], preds)
        for split_name, preds in fitted["predictions_by_split"].items()
    }
    yearly_metrics = {
        split_name: compute_yearly_metrics(splits[split_name], preds)
        for split_name, preds in fitted["predictions_by_split"].items()
        if split_name in {"val_select", "val_eval"}
    }
    metrics_rows = []
    for split_name, metrics in split_metrics.items():
        for metric_name, payload in metrics.items():
            target_name, horizon = metric_name.rsplit("_", 1)
            row = {
                "representation": job["representation"],
                "model_key": job["model_key"],
                "seed": job["seed"],
                "split_name": split_name,
                "target_name": target_name,
                "horizon": f"H{horizon}",
            }
            row.update(payload if target_name == "simple_trade" else {"spearman": payload.get("spearman")})
            metrics_rows.append(row)
    preview = fitted["predictions_by_split"]["val_eval"].head(8).copy()
    preview.insert(0, "split_name", "val_eval")
    preview.insert(0, "seed", int(job["seed"]))
    preview.insert(0, "model_key", job["model_key"])
    preview.insert(0, "representation", job["representation"])
    preview["time"] = splits["val_eval"]["time"].head(len(preview)).astype(str).to_list()
    return {
        "job_key": job_key(job),
        "representation": job["representation"],
        "model_key": job["model_key"],
        "seed": int(job["seed"]),
        "elapsed_sec": time.time() - started,
        "rows": {split: int(len(frame)) for split, frame in splits.items() if split in {"train", "val_select", "val_eval", "low_n_disclosure"}},
        "token_count": 100,
        "token_feature_count": len(TOKEN_FEATURE_NAMES),
        "batch_size": fitted["batch_size"],
        "device": fitted["device"],
        "torch_thread_count": fitted["torch_thread_count"],
        "status": "completed",
        "normalization_contract": normalization_contract,
        "target_normalization_contract": {
            "fit_split": data.target_normalizer.fit_split,
            "target_order": data.target_normalizer.target_order,
            "scaler": "median_iqr",
            "center": data.target_normalizer.center,
            "scale": data.target_normalizer.scale,
            "scale_floor": 1e-6,
            "clip": [-10.0, 10.0],
            "input_and_target_scalers_separate": True,
            "inverse_transform_before_metrics": True,
        },
        "model_metadata": fitted["model_metadata"],
        "split_metrics": split_metrics,
        "yearly_metrics": yearly_metrics,
        "metrics_rows": metrics_rows,
        "rows_preview": preview,
    }


def _dependency_versions() -> dict[str, str]:
    versions = {"python": sys.version.split()[0]}
    for mod_name in ("numpy", "pandas", "sklearn", "torch"):
        try:
            mod = __import__(mod_name)
            versions[mod_name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[mod_name] = "not_installed"
    return versions


def build_run_config(threads: int = 24, max_epochs: int = 60, batch_size: int = 512, device: str = "auto") -> dict[str, object]:
    return {
        "schema_version": SEQUENCE_TRANSFORMER_SCHEMA_VERSION,
        "representations": SEQUENCE_TRANSFORMER_REPRESENTATIONS,
        "models": SEQUENCE_TRANSFORMER_MODEL_KEYS,
        "horizons": TARGET_HORIZONS,
        "predicted_target_families": PREDICTED_TARGET_FAMILIES,
        "seeds": SEQUENCE_TRANSFORMER_SEEDS,
        "token_feature_names": TOKEN_FEATURE_NAMES,
        "sequence_order": "token index 0 = fractal0 newest; token index 99 = fractal99 oldest",
        "mask_contract": {"valid_token": True, "padding_token": False, "padding_value": 0.0},
        "split_policy": {
            "train": "<=2020",
            "validation": "2021-2025 split into val_select/val_eval",
            "low_n_disclosure": "2026 disclosure_only",
            "locked_test": "not_opened",
            "embargo_hours": max(TARGET_HORIZONS),
        },
        "normalization_config": {
            "input_scaler": "median_iqr",
            "fit_split": "train",
            "valid_tokens_only": True,
            "scale_floor": 1e-6,
            "clip": [-10.0, 10.0],
            "padding_after_transform": 0.0,
        },
        "target_normalization_config": {
            "target_order": TARGET_COLUMNS,
            "scaler": "median_iqr",
            "fit_split": "train",
            "scale_floor": 1e-6,
            "clip": [-10.0, 10.0],
            "inverse_transform_before_metrics": True,
        },
        "selection_policy": SELECTION_POLICY,
        "training_policy": {**TRAINING_POLICY, "epochs": max_epochs},
        "output_schema": {
            "json_top_level": (
                "schema_version",
                "verdict",
                "dependency_versions",
                "normalization_contract",
                "target_normalization_contract",
                "selection_policy",
                "training_policy",
                "run_config_hash",
                "summary",
                "run_config",
                "progress",
                "runs",
                "failed_runs",
                "entry_based_smoke_check",
                "split_horizon_overlap_check",
                "tensor_audit",
                "metrics",
                "best_by_val_select",
                "best_by_val_eval_disclosure",
                "yearly_metrics",
            )
        },
        "threads": threads,
        "batch_size": batch_size,
        "device": device,
        "dependency_versions": _dependency_versions(),
        "output_prefix": SEQUENCE_TRANSFORMER_OUTPUT_PREFIX,
    }


def compute_run_config_hash(config: dict[str, object]) -> str:
    payload = json.dumps(config, sort_keys=True, default=_json_default).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_resume_report(path: Path, current_hash: str) -> dict[str, object]:
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("run_config_hash") != current_hash:
        raise ValueError("run_config_hash mismatch; refuse to resume incompatible run")
    return report


def _json_default(value: object) -> object:
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.to_dict()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return str(value)


def save_sequence_report(report: dict[str, object], path: Path) -> None:
    run_config = report.get("run_config", {})
    summary = report.get("summary", {})
    if isinstance(run_config, dict):
        report["schema_version"] = run_config.get("schema_version", SEQUENCE_TRANSFORMER_SCHEMA_VERSION)
        report["dependency_versions"] = run_config.get("dependency_versions", {})
    if isinstance(summary, dict):
        report["verdict"] = summary.get("verdict", report.get("verdict"))
    report.setdefault("selection_policy", SELECTION_POLICY)
    report.setdefault("training_policy", TRAINING_POLICY)
    report.setdefault("normalization_contract", {
        "scope": "sequence_tokens",
        "fit_split": "train",
        "scaler": "median_iqr",
        "scale_floor": 1e-6,
        "clip": [-10.0, 10.0],
        "padding_values": 0.0,
        "padding_excluded_from_fit": True,
        "validation_splits_do_not_fit": ("val_select", "val_eval", "low_n_disclosure"),
    })
    report.setdefault("target_normalization_contract", {
        "fit_split": "train",
        "target_order": TARGET_COLUMNS,
        "scaler": "median_iqr",
        "scale_floor": 1e-6,
        "clip": [-10.0, 10.0],
        "input_and_target_scalers_separate": True,
        "inverse_transform_before_metrics": True,
    })
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = json.loads(json.dumps(report, ensure_ascii=True, indent=2, default=_json_default))
    path.write_text(json.dumps(serializable, ensure_ascii=True, indent=2), encoding="utf-8")


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _heartbeat(label: str, done_runs: int, total_runs: int, started: float) -> None:
    elapsed = time.time() - started
    eta = (elapsed / done_runs * (total_runs - done_runs)) if done_runs else None
    eta_text = "unknown" if eta is None else f"{eta:.1f}s"
    print(f"[heartbeat] {label}: done_runs={done_runs}/{total_runs}, elapsed={elapsed:.1f}s, eta={eta_text}", flush=True)
    _append_run_log(f"[heartbeat] {label}: done_runs={done_runs}/{total_runs}, elapsed={elapsed:.1f}s, eta={eta_text}")


def _append_run_log(line: str) -> None:
    REPORT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _utc_now_iso()
    with REPORT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {line}\n")


def _resolve_device(device: str) -> str:
    if device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but not available")
        return "cuda"
    if device == "auto" and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _load_sequence_splits() -> dict[str, pd.DataFrame]:
    old_splits = powerful._add_h24_targets_if_missing(closeout.base.load_entry_based_splits(target_mode="rebuilt"))
    splits = powerful._convert_splits(old_splits)
    splits.update(powerful._split_validation_roles(splits["validation"]))
    splits = powerful.apply_horizon_embargo(splits, max_horizon_hours=max(TARGET_HORIZONS))
    missing = {
        split_name: [column for column in TARGET_COLUMNS if column not in frame.columns]
        for split_name, frame in splits.items()
        if isinstance(frame, pd.DataFrame) and split_name in {"train", "validation", "val_select", "val_eval", "low_n_disclosure"}
    }
    missing = {split_name: columns for split_name, columns in missing.items() if columns}
    if missing:
        raise RuntimeError(f"required entry targets missing after H24 rebuild: {missing}")
    return splits


def run_sequence_transformer(args: argparse.Namespace) -> dict[str, object]:
    started = time.time()
    if not args.resume and REPORT_LOG_PATH.exists():
        REPORT_LOG_PATH.unlink()
    args.resolved_device = _resolve_device(args.device)
    jobs = enumerate_sequence_transformer_jobs()
    run_config = build_run_config(args.threads, args.max_epochs, args.batch_size, args.device)
    run_config_hash = compute_run_config_hash(run_config)
    _heartbeat("preflight", 0, len(jobs), started)

    report: dict[str, object]
    if args.resume and REPORT_JSON_PATH.exists():
        report = load_resume_report(REPORT_JSON_PATH, run_config_hash)
    else:
        report = {
            "schema_version": SEQUENCE_TRANSFORMER_SCHEMA_VERSION,
            "stage_status": "DIAGNOSTIC_ONLY",
            "started_at": _utc_now_iso(),
            "run_config": run_config,
            "run_config_hash": run_config_hash,
            "runs": [],
            "failed_runs": [],
            "selection_policy": SELECTION_POLICY,
            "training_policy": {**TRAINING_POLICY, "epochs": args.max_epochs},
        }

    splits = _load_sequence_splits()
    report["target_normalization_contract"] = build_target_normalization_contract(splits["train"])
    smoke = run_sequence_smoke_check({k: splits[k] for k in ("train", "val_select", "val_eval", "low_n_disclosure")})
    overlap = split_horizon_overlap_check(splits)
    report["entry_based_smoke_check"] = smoke
    report["split_horizon_overlap_check"] = overlap
    _heartbeat("tensor_build", len(report.get("runs", [])), len(jobs), started)
    audit_tensors = {split: build_sequence_tensor(splits[split], "all100_sequence") for split in ("train", "val_select", "val_eval", "low_n_disclosure")}
    tensor_audit = audit_sequence_tensor(audit_tensors)
    report["tensor_audit"] = tensor_audit
    save_sequence_report(report, REPORT_JSON_PATH)
    if smoke["status"] != "PASS" or overlap["status"] != "PASS" or tensor_audit["status"] == "ERROR":
        report["summary"] = {
            "verdict": "ABORT_CONTRACT_FAIL",
            "smoke_status": smoke["status"],
            "split_horizon_overlap_status": overlap["status"],
            "tensor_audit_status": tensor_audit["status"],
        }
        report["progress"] = {"done_runs": len(report.get("runs", [])), "total_runs": len(jobs), "finished_at": _utc_now_iso(), "elapsed_sec": time.time() - started}
        save_sequence_report(report, REPORT_JSON_PATH)
        return report

    completed = {run.get("job_key") for run in report.get("runs", [])}
    failed_runs: list[dict[str, object]] = list(report.get("failed_runs", []))
    for index, job in enumerate(jobs, start=1):
        key = job_key(job)
        if key in completed:
            continue
        _heartbeat(f"run_start:{key}", len(report.get("runs", [])), len(jobs), started)
        try:
            run = evaluate_sequence_job(job, splits, args)
            report.setdefault("runs", []).append(run)
        except Exception as exc:
            failed_runs.append({
                "job_key": key,
                "representation": job["representation"],
                "model_key": job["model_key"],
                "seed": job["seed"],
                "elapsed_sec": time.time() - started,
                "exception_type": type(exc).__name__,
                "error_text": str(exc),
            })
        report["failed_runs"] = failed_runs
        report["progress"] = {"done_runs": len(report.get("runs", [])), "total_runs": len(jobs), "current_job_index": index, "elapsed_sec": time.time() - started}
        save_sequence_report(report, REPORT_JSON_PATH)
        _heartbeat(f"run_end:{key}", len(report.get("runs", [])), len(jobs), started)

    rows = score_sequence_predictions(report.get("runs", []))
    summary = decide_sequence_verdict(rows, smoke, tensor_audit)
    report["metrics"] = rows
    report["summary"] = summary
    report["best_by_val_select"] = select_winner_by_policy(rows, SELECTION_POLICY)
    by_eval = dict(max(rows, key=lambda row: float(row.get("val_eval", 0.0) or 0.0), default={}))
    by_eval["selection_forbidden"] = True
    report["best_by_val_eval_disclosure"] = by_eval
    report["yearly_metrics"] = {run["job_key"]: run.get("yearly_metrics", {}) for run in report.get("runs", [])}
    report["progress"] = {"done_runs": len(report.get("runs", [])), "total_runs": len(jobs), "finished_at": _utc_now_iso(), "elapsed_sec": time.time() - started}
    pd.DataFrame(rows).to_csv(REPORT_METRICS_PATH, index=False)
    previews = [pd.DataFrame(run["rows_preview"]) for run in report.get("runs", []) if run.get("rows_preview") is not None]
    (pd.concat(previews, ignore_index=True) if previews else pd.DataFrame()).to_csv(REPORT_ROWS_PATH, index=False)
    pd.DataFrame(tensor_audit.get("warnings", []) + tensor_audit.get("errors", [])).to_csv(REPORT_TENSOR_AUDIT_PATH, index=False)
    save_sequence_report(report, REPORT_JSON_PATH)
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Entry-based fractal sequence transformer runner")
    parser.add_argument("--entry-based-sequence-transformer", action="store_true")
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cpu")
    parser.add_argument("--threads", type=int, default=24)
    parser.add_argument("--max-epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=512)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if not args.entry_based_sequence_transformer:
        print("Pass --entry-based-sequence-transformer")
        return 1
    run_sequence_transformer(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
